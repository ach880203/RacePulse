// =============================================================================
// IntroVideo.tsx — 처음 방문한 사용자에게만 인트로 영상을 보여주는 컴포넌트
// =============================================================================
// 이 파일의 핵심 목적:
// 1) 사용자가 인트로를 이미 봤는지 localStorage에서 확인합니다.
// 2) 처음 방문이면 영상을 충분히 불러온 뒤 자연스럽게 재생합니다.
// 3) 영상이 끝나거나 사용자가 건너뛰기를 누르면 메인 화면으로 이동합니다.
// =============================================================================

// React의 useCallback = 같은 함수를 재사용해 Hook 의존성 경고와 불필요한 재생성을 줄이는 도구
// React의 useEffect = 화면이 나타나거나 사라질 때 부가 작업을 처리하는 도구
// React의 useRef = 화면을 다시 그리지 않고도 값을 기억하는 보관함
// React의 useState = 화면에 보여줄 상태값을 저장하는 도구
import { useCallback, useEffect, useRef, useState } from 'react'

// localStorage에 저장할 키 이름을 한 곳에 모아두면
// 여러 파일에서 같은 문자열을 반복하지 않아도 되고, 오타도 줄일 수 있습니다.
export const INTRO_WATCHED_STORAGE_KEY = 'racepulse_intro_watched'

// 정적 자산 경로를 영문으로 고정해 두면 개발/빌드 환경마다 인코딩 차이로 깨질 가능성을 줄일 수 있습니다.
const INTRO_VIDEO_SOURCE = '/intro-video.mp4'

// WebM은 같은 화질에서 MP4보다 더 작아질 수 있는 영상 포맷입니다.
// 변환 명령 예시: ffmpeg -i intro-video.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 intro-video.webm
const INTRO_VIDEO_WEBM_SOURCE = '/intro-video.webm'

// 포스터 이미지는 영상이 재생되기 전 사용자가 보게 될 첫 정지 화면입니다.
const INTRO_POSTER_SOURCE = '/intro-poster.jpg'

// 너무 오래 기다리게 하지 않기 위해 10초 후 자동 건너뛰기를 적용합니다.
const VIDEO_BUFFER_TIMEOUT_MS = 10_000

// CSS의 fadeOut 시간과 자바스크립트 전환 시간을 맞추기 위한 상수입니다.
const FADE_OUT_DURATION_MS = 500

// 부모 컴포넌트가 "인트로 종료" 시점을 알 수 있도록 콜백 함수를 받습니다.
type IntroVideoProps = {
  onComplete: () => void
}

function IntroVideo({ onComplete }: IntroVideoProps) {
  // 실제 <video> 태그를 직접 제어하기 위한 ref입니다.
  const videoElementRef = useRef<HTMLVideoElement | null>(null)

  // 부모가 다시 렌더링되어도 최신 onComplete 함수를 계속 참조하기 위한 ref입니다.
  const onCompleteRef = useRef(onComplete)

  // setTimeout ID를 기억해두면 컴포넌트가 사라질 때 안전하게 정리할 수 있습니다.
  const bufferTimeoutRef = useRef<number | null>(null)
  const exitTimeoutRef = useRef<number | null>(null)

  // 종료 처리가 여러 번 겹치는 것을 막는 안전장치입니다.
  const hasFinishedIntroRef = useRef(false)

  // 실제 재생이 시작되기 전까지는 로딩 UI를 보여주기 위한 상태값입니다.
  const [hasPlaybackStarted, setHasPlaybackStarted] = useState(false)

  // 페이드 아웃 클래스를 붙일지 결정하는 상태값입니다.
  const [isFadingOut, setIsFadingOut] = useState(false)

  // 버퍼링 타이머를 정리하는 공통 함수입니다.
  const clearBufferTimeout = useCallback(() => {
    if (bufferTimeoutRef.current !== null) {
      window.clearTimeout(bufferTimeoutRef.current)
      bufferTimeoutRef.current = null
    }
  }, [])

  // 메인 화면 전환 타이머도 별도로 정리할 수 있게 분리합니다.
  const clearExitTimeout = useCallback(() => {
    if (exitTimeoutRef.current !== null) {
      window.clearTimeout(exitTimeoutRef.current)
      exitTimeoutRef.current = null
    }
  }, [])

  // 이 함수는 영상 종료, 스킵, 자동 타임아웃, 재생 실패를 모두 같은 흐름으로 처리합니다.
  // 종료 로직을 한 곳에 모아야 동작이 어긋나지 않습니다.
  const finishIntro = useCallback(() => {
    if (hasFinishedIntroRef.current) {
      return
    }

    hasFinishedIntroRef.current = true
    clearBufferTimeout()
    clearExitTimeout()
    setIsFadingOut(true)

    // localStorage = 브라우저 안에 데이터를 오래 저장하는 공간입니다.
    // 새로고침 후에도 남기 때문에 "이미 본 인트로" 표시용으로 적합합니다.
    try {
      localStorage.setItem(INTRO_WATCHED_STORAGE_KEY, 'true')
    } catch (error) {
      // 저장이 실패해도 화면이 멈추면 안 되므로 로그만 남기고 계속 진행합니다.
      console.error('인트로 시청 상태 저장에 실패했습니다.', error)
    }

    // 즉시 화면을 바꾸면 페이드 아웃이 보이지 않으므로 0.5초 뒤에 완료를 알립니다.
    exitTimeoutRef.current = window.setTimeout(() => {
      onCompleteRef.current()
    }, FADE_OUT_DURATION_MS)
  }, [clearBufferTimeout, clearExitTimeout])

  // canplaythrough 이후 실제 재생을 요청하는 함수입니다.
  // 자동 재생이 막히는 드문 환경에서는 사용자가 멈춰 있지 않도록 바로 종료 처리합니다.
  const requestVideoPlayback = useCallback(() => {
    const videoElement = videoElementRef.current

    if (!videoElement || hasFinishedIntroRef.current) {
      return
    }

    clearBufferTimeout()

    const playPromise = videoElement.play()

    if (playPromise !== undefined) {
      playPromise.catch((error) => {
        console.error('인트로 영상 자동 재생에 실패했습니다.', error)
        finishIntro()
      })
    }
  }, [clearBufferTimeout, finishIntro])

  // 최신 onComplete 함수를 ref에 반영합니다.
  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  // 이 블록이 하는 일:
  // 1) 이미 본 인트로인지 확인
  // 2) 10초 버퍼링 제한 타이머 시작
  // 3) 캐시된 영상이면 즉시 재생 시도
  // 4) 컴포넌트가 사라질 때 타이머 정리
  useEffect(() => {
    try {
      const watchedValue = localStorage.getItem(INTRO_WATCHED_STORAGE_KEY)

      if (watchedValue === 'true') {
        onCompleteRef.current()
        return undefined
      }
    } catch (error) {
      // 읽기 실패는 치명적이지 않으므로, 로그만 남기고 인트로를 계속 시도합니다.
      console.error('인트로 시청 상태 확인에 실패했습니다.', error)
    }

    bufferTimeoutRef.current = window.setTimeout(() => {
      finishIntro()
    }, VIDEO_BUFFER_TIMEOUT_MS)

    const videoElement = videoElementRef.current

    // readyState >= HAVE_ENOUGH_DATA 는
    // 브라우저가 "이제 끊김 없이 끝까지 재생 가능하다"고 판단한 상태입니다.
    if (videoElement && videoElement.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA) {
      requestVideoPlayback()
    }

    return () => {
      clearBufferTimeout()
      clearExitTimeout()
    }
  }, [clearBufferTimeout, clearExitTimeout, finishIntro, requestVideoPlayback])

  return (
    <div className={`intro-video-shell ${isFadingOut ? 'intro-video-shell--fade-out' : ''}`}>
      {/* --------------------------------------------------------------------
          이 블록이 하는 일:
          전체 화면에 포스터/영상을 깔고, 준비가 끝나면 자연스럽게 재생합니다.
          muted를 넣은 이유는 모바일/브라우저 자동 재생 제한을 피하기 위해서입니다.
          -------------------------------------------------------------------- */}
      <video
        ref={videoElementRef}
        className="intro-video-player"
        preload="auto"
        poster={INTRO_POSTER_SOURCE}
        muted
        playsInline
        onCanPlayThrough={requestVideoPlayback}
        onPlaying={() => {
          clearBufferTimeout()
          setHasPlaybackStarted(true)
        }}
        onEnded={() => {
          finishIntro()
        }}
        onError={() => {
          finishIntro()
        }}
      >
        <source src={INTRO_VIDEO_WEBM_SOURCE} type="video/webm" />
        <source src={INTRO_VIDEO_SOURCE} type="video/mp4" />
      </video>

      {/* --------------------------------------------------------------------
          이 블록이 하는 일:
          영상이 아직 재생되지 않았을 때 중앙 로딩 바와 안내 문구를 보여줍니다.
          opacity만 바꾸는 이유는 레이아웃 흔들림 없이 부드럽게 숨기기 위해서입니다.
          -------------------------------------------------------------------- */}
      <div className={`intro-video-loading ${hasPlaybackStarted ? 'intro-video-loading--hidden' : ''}`}>
        <div className="intro-video-loading__bar" aria-hidden="true" />
        <p className="intro-video-loading__text">레이스펄스를 불러오는 중...</p>
      </div>

      {/* --------------------------------------------------------------------
          이 블록이 하는 일:
          사용자가 기다리지 않고 바로 넘어가고 싶을 때를 위한 안전한 탈출 버튼입니다.
          영상이 끊기거나 네트워크가 느려도 사용자가 직접 흐름을 제어할 수 있습니다.
          -------------------------------------------------------------------- */}
      <button
        type="button"
        className="intro-video-skip-button"
        onClick={() => {
          finishIntro()
        }}
      >
        건너뛰기
      </button>
    </div>
  )
}

export default IntroVideo
