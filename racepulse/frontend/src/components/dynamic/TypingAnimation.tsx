import { useEffect, useState } from 'react'

interface TypingAnimationProps {
  text: string
  speed?: number
}

function TypingAnimation({ text, speed = 35 }: TypingAnimationProps) {
  const [visibleText, setVisibleText] = useState('')

  useEffect(() => {
    let index = 0
    const timer = window.setInterval(() => {
      index += 1
      setVisibleText(text.slice(0, index))
      if (index >= text.length) window.clearInterval(timer)
    }, speed)
    return () => window.clearInterval(timer)
  }, [speed, text])

  return (
    <p className="text-white/80">
      {visibleText}
      <span className="ml-1 animate-pulse text-brand-gold-400">|</span>
    </p>
  )
}

export default TypingAnimation
