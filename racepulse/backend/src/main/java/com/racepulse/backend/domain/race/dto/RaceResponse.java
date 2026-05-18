package com.racepulse.backend.domain.race.dto;

import java.time.DayOfWeek; // 요일을 비교할 때 사용하는 자바 기본 날짜 라이브러리입니다.
import java.time.LocalDate; // 시간 없이 날짜만 다룰 때 사용하는 자바 기본 날짜 라이브러리입니다.
import java.time.LocalDateTime; // 날짜와 시간을 함께 다루되, 시간대 정보는 없는 자바 기본 날짜 라이브러리입니다.
import java.time.LocalTime; // 날짜 없이 시간만 다룰 때 사용하는 자바 기본 시간 라이브러리입니다.
import java.time.ZoneId; // "Asia/Seoul"처럼 지역별 시간대를 지정할 때 사용하는 자바 기본 시간대 라이브러리입니다.
import java.time.ZonedDateTime; // 날짜, 시간, 시간대를 함께 다룰 때 사용하는 자바 기본 날짜/시간 라이브러리입니다.
import java.time.temporal.TemporalAdjusters; // "다음 목요일"처럼 날짜를 규칙에 맞게 이동시킬 때 사용하는 자바 기본 날짜 도구입니다.

import com.racepulse.backend.domain.race.entity.Race; // DB 경주 정보를 API 응답 DTO로 바꾸기 위해 사용하는 엔티티입니다.
import com.racepulse.backend.domain.race.entity.RaceStatus; // 경주 상태별 응답 상태값을 계산하기 위해 사용하는 enum입니다.

import lombok.AllArgsConstructor; // 모든 final 필드를 받는 생성자를 Lombok이 자동으로 만들어 주는 라이브러리입니다.
import lombok.Builder; // 필드가 많을 때 .id(...).status(...)처럼 읽기 쉬운 객체 생성 코드를 만들어 주는 라이브러리입니다.
import lombok.Getter; // private 필드를 JSON 응답으로 꺼내 쓸 수 있도록 getter 메서드를 자동 생성하는 라이브러리입니다.

// 경주 목록 화면에 필요한 최소 필드만 담는 응답 DTO입니다.
@Getter
@Builder
@AllArgsConstructor
public class RaceResponse {

    // 서버가 어느 지역에서 실행되든 한국 경마 일정은 한국 시간 기준으로 판단해야 하므로 시간대를 상수로 고정합니다.
    private static final ZoneId KST = ZoneId.of("Asia/Seoul");

    // FE가 화면에서 그대로 비교하기 쉽도록 상태 문자열을 상수로 모아 둡니다.
    private static final String DATA_STATUS_READY = "READY";
    private static final String DATA_STATUS_UPDATING = "UPDATING";
    private static final String DATA_STATUS_COLLECTED = "COLLECTED";

    private final Long id;
    private final String meetCode;
    private final LocalDate rcDate;
    private final Integer raceNo;
    private final String raceName;
    private final Integer distance;
    private final String status;
    private final LocalTime startTime;
    private final String lastUpdated;
    private final String dataStatus;
    private final String nextUpdate;

    public static RaceResponse from(Race race) {
        // @Builder는 생성자 인자 순서를 외우지 않고 필드 이름으로 값을 채우게 해 주는 패턴입니다.
        // dataStatus는 nextUpdate 계산에도 필요하므로 먼저 변수에 담아 같은 기준값을 재사용합니다.
        String dataStatus = resolveDataStatus(race);

        return RaceResponse.builder()
                .id(race.getId())
                .meetCode(race.getMeetCode().name())
                .rcDate(race.getRcDate())
                .raceNo(race.getRaceNo())
                .raceName(race.getRaceName())
                .distance(race.getDistance())
                .status(race.getStatus().name())
                .startTime(race.getStartTime())
                .lastUpdated(resolveLastUpdated(race))
                .dataStatus(dataStatus)
                .nextUpdate(resolveNextUpdate(race, dataStatus))
                .build();
    }

    private static String resolveLastUpdated(Race race) {
        // updatedAt은 DB가 마지막으로 수정한 시각입니다. 아직 값이 없을 수 있으므로 null을 먼저 확인합니다.
        LocalDateTime updatedAt = race.getUpdatedAt();

        if (updatedAt == null) {
            return null;
        }

        // DB의 LocalDateTime에는 시간대 정보가 없으므로 한국 시간으로 해석한 뒤 UTC 문자열로 바꿉니다.
        // UTC는 국제 표준 시간이라 FE가 사용자 지역 시간으로 변환하거나 최신성 표시를 만들기 쉽습니다.
        return updatedAt.atZone(KST)
                .toInstant()
                .toString();
    }

    private static String resolveDataStatus(Race race) {
        // private static 헬퍼 메서드로 분리하면 from()은 값 조립만 담당하고, 상태 판단 규칙은 여기서만 관리할 수 있습니다.
        RaceStatus status = race.getStatus();
        LocalDate rcDate = race.getRcDate();
        LocalDate today = LocalDate.now(KST);

        if (status == RaceStatus.COMPLETED) {
            // COLLECTED는 수집이 끝난 상태이므로 화면에서 "최신 데이터 확보" 같은 의미로 사용할 수 있습니다.
            return DATA_STATUS_COLLECTED;
        }

        if (status == RaceStatus.CANCELLED) {
            // 취소 경주는 추가 수집이 필요한 진행 중 데이터가 아니므로 화면에서는 준비 상태로 보여 줍니다.
            return DATA_STATUS_READY;
        }

        if (rcDate.isEqual(today) && status == RaceStatus.SCHEDULED) {
            // 오늘 예정된 경주는 실제 결과 수집이 진행될 수 있으므로 화면에서 갱신 중 상태로 표시합니다.
            return DATA_STATUS_UPDATING;
        }

        if (rcDate.isBefore(today) && status == RaceStatus.SCHEDULED) {
            // 과거 예정 상태는 아직 완료 플래그가 안 바뀐 데이터일 수 있어, FE에는 수집 완료로 취급해 혼란을 줄입니다.
            return DATA_STATUS_COLLECTED;
        }

        if (rcDate.isAfter(today)) {
            // 미래 경주는 아직 결과 수집 전이므로 화면에서 준비 상태로 표시합니다.
            return DATA_STATUS_READY;
        }

        return DATA_STATUS_READY;
    }

    private static String resolveNextUpdate(Race race, String dataStatus) {
        LocalDate rcDate = race.getRcDate();

        if (DATA_STATUS_COLLECTED.equals(dataStatus)) {
            // 이미 수집이 끝난 데이터는 다음 갱신 예정이 없으므로 null을 내려 FE가 예정 문구를 숨길 수 있게 합니다.
            return null;
        }

        if (DATA_STATUS_READY.equals(dataStatus)) {
            return resolveReadyNextUpdate(rcDate);
        }

        if (DATA_STATUS_UPDATING.equals(dataStatus)) {
            return resolveUpdatingNextUpdate();
        }

        return null;
    }

    private static String resolveReadyNextUpdate(LocalDate rcDate) {
        DayOfWeek raceDayOfWeek = rcDate.getDayOfWeek();

        if (raceDayOfWeek == DayOfWeek.SATURDAY
                || raceDayOfWeek == DayOfWeek.SUNDAY
                || raceDayOfWeek == DayOfWeek.MONDAY) {
            // 토/일/월 경주는 경주 당일 09:05 KST 수집 일정을 UTC 문자열로 바꿔 내려줍니다.
            return toUtcString(rcDate, LocalTime.of(9, 5));
        }

        // TemporalAdjusters.next(...)는 기준 날짜 이후에 처음 만나는 지정 요일을 찾아 줍니다.
        // 예를 들어 화요일 경주는 그 다음 목요일 10:00 KST에 다시 수집될 수 있다고 FE에 알려 줍니다.
        LocalDate nextThursday = rcDate.with(TemporalAdjusters.next(DayOfWeek.THURSDAY));
        return toUtcString(nextThursday, LocalTime.of(10, 0));
    }

    private static String resolveUpdatingNextUpdate() {
        ZonedDateTime now = ZonedDateTime.now(KST);
        LocalDate today = now.toLocalDate();
        LocalTime currentTime = now.toLocalTime();

        if (currentTime.isBefore(LocalTime.of(8, 0))) {
            // 오늘 수집이 시작되기 전이면 08:00 KST를 다음 확인 시각으로 내려줍니다.
            return toUtcString(today, LocalTime.of(8, 0));
        }

        if (currentTime.isBefore(LocalTime.of(9, 5))) {
            // 08:00 이후 09:05 전에는 주요 수집 예정 시각인 09:05 KST를 다음 확인 시각으로 내려줍니다.
            return toUtcString(today, LocalTime.of(9, 5));
        }

        // 09:05 이후에는 당일 자동 갱신 예정이 없다고 보고 null을 내려 FE가 예정 문구를 숨기게 합니다.
        return null;
    }

    private static String toUtcString(LocalDate date, LocalTime time) {
        // KST로 만든 날짜/시간을 Instant로 바꾸면 "2026-05-15T00:05:00Z" 같은 UTC ISO-8601 문자열이 됩니다.
        return ZonedDateTime.of(date, time, KST)
                .toInstant()
                .toString();
    }
}
