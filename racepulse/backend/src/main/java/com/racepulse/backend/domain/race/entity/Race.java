package com.racepulse.backend.domain.race.entity;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;

import org.hibernate.annotations.JdbcType;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.dialect.PostgreSQLEnumJdbcType;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

// =============================================================================
// Race.java — races 테이블 한 줄을 자바 객체로 표현하는 엔티티
// =============================================================================
// 아직 데이터가 없더라도 엔티티를 먼저 정확히 만들어야
// JPA가 테이블 구조를 검증(validate)하고 나중에 데이터를 안정적으로 읽을 수 있습니다.
// =============================================================================

@Getter
@Entity
@Table(name = "races")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Race {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    @Column(name = "meet_code", nullable = false, length = 10)
    private MeetCode meetCode;

    @Column(name = "rc_date", nullable = false)
    private LocalDate rcDate;

    @Column(name = "race_no", nullable = false)
    private Integer raceNo;

    @Column(name = "race_name", nullable = false, length = 150)
    private String raceName;

    @Column(nullable = false)
    private Integer distance;

    @Column(name = "track_type", length = 50)
    private String trackType;

    // PostgreSQL enum 컬럼은 일반 문자열로 비교하면 DB에서 타입 오류가 납니다.
    // Hibernate가 파라미터를 track_condition enum 타입으로 보내도록 전용 타입을 지정합니다.
    @JdbcType(PostgreSQLEnumJdbcType.class)
    @Enumerated(EnumType.STRING)
    @Column(name = "track_condition", columnDefinition = "track_condition")
    private TrackCondition trackCondition;

    // 실제 운영 DB에서는 상금 컬럼이 bigint로 만들어져 있으므로 Long으로 맞춥니다.
    @Column(name = "prize_money")
    private Long prizeMoney;

    @Column(length = 50)
    private String weather;

    @Column(name = "start_time")
    private LocalTime startTime;

    // PostgreSQL enum 컬럼은 일반 문자열로 비교하면 DB에서 타입 오류가 납니다.
    // /api/v1/races?status=SCHEDULED 조회 조건도 race_status enum 타입으로 바인딩합니다.
    @JdbcType(PostgreSQLEnumJdbcType.class)
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, columnDefinition = "race_status")
    private RaceStatus status;

    @Column(name = "race_class", length = 50)
    private String raceClass;

    // race_grade는 "일반/중요/특별/국제"처럼 한글 값도 올 수 있으므로 String으로 둡니다.
    @Column(name = "race_grade", length = 50)
    private String raceGrade;

    @Column(name = "front_count")
    private Integer frontCount;

    // PostgreSQL enum 컬럼은 일반 문자열로 비교하면 DB에서 타입 오류가 납니다.
    // 조회/저장 시 pace_scenario enum 타입으로 안전하게 주고받습니다.
    @JdbcType(PostgreSQLEnumJdbcType.class)
    @Enumerated(EnumType.STRING)
    @Column(name = "pace_scenario", columnDefinition = "pace_scenario")
    private PaceScenario paceScenario;

    // PostgreSQL enum 컬럼은 일반 문자열로 비교하면 DB에서 타입 오류가 납니다.
    // 조회/저장 시 pace_advantage enum 타입으로 안전하게 주고받습니다.
    @JdbcType(PostgreSQLEnumJdbcType.class)
    @Enumerated(EnumType.STRING)
    @Column(name = "pace_advantage", columnDefinition = "pace_advantage")
    private PaceAdvantage paceAdvantage;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
}
