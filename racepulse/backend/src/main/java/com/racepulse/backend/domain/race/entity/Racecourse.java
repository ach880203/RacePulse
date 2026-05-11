package com.racepulse.backend.domain.race.entity;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

// @CreationTimestamp = insert 시각을 하이버네이트가 자동으로 넣어줍니다.
import org.hibernate.annotations.CreationTimestamp;
// @JdbcTypeCode = JSONB 같은 특수 타입을 어떻게 저장할지 하이버네이트에 알려줍니다.
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

// @Column = DB 컬럼 이름, 길이, null 허용 여부 등을 지정합니다.
import jakarta.persistence.Column;
// @Entity = 이 클래스가 DB 테이블과 연결된다는 뜻입니다.
import jakarta.persistence.Entity;
// @EnumType/@Enumerated = enum을 DB에 어떤 방식(문자/숫자)으로 저장할지 정합니다.
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
// @GeneratedValue = id 값을 DB가 자동 증가로 만들어주게 합니다.
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
// @Id = 기본 키(primary key) 필드라는 뜻입니다.
import jakarta.persistence.Id;
// @Table = 실제 DB 테이블 이름을 지정합니다.
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

// =============================================================================
// Racecourse.java — racecourses 테이블과 연결되는 엔티티
// =============================================================================
// 엔티티(Entity)는 "DB 한 줄(row)을 자바 객체 하나로 표현한 것"이라고 이해하면 쉽습니다.
// =============================================================================

@Getter
@Entity
@Table(name = "racecourses")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Racecourse {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 경마장 코드(SC/BU/JJ)는 허용값이 정해져 있으므로 enum으로 다룹니다.
    @Enumerated(EnumType.STRING)
    @Column(name = "meet_code", nullable = false, length = 10)
    private MeetCode meetCode;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, length = 255)
    private String location;

    // JSONB 컬럼을 List<String>으로 바로 다루기 위한 설정입니다.
    // 예: ["모래", "잔디"] 같은 배열 데이터를 자바 리스트로 읽고 씁니다.
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "track_types", nullable = false, columnDefinition = "jsonb")
    private List<String> trackTypes = new ArrayList<>();

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
}
