package com.racepulse.backend.domain.horse.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import com.racepulse.backend.domain.race.entity.MeetCode;

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
// Horse.java — horses 테이블과 연결되는 경주마 엔티티
// =============================================================================
// 응답에 필요한 필드뿐 아니라 테이블 핵심 필드를 함께 연결해두면
// 나중에 상세 조회나 검색 API를 확장할 때 다시 구조를 뜯어고칠 일이 줄어듭니다.
// =============================================================================

@Getter
@Entity
@Table(name = "horses")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Horse {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(name = "eng_name", length = 100)
    private String engName;

    @Column(name = "birth_year")
    private Integer birthYear;

    // 성별 값 형식이 아직 확정되지 않았으므로 우선 문자열로 받아 둡니다.
    @Column(length = 20)
    private String sex;

    @Column(length = 50)
    private String color;

    @Column(length = 50)
    private String origin;

    @Column(name = "father_name", length = 100)
    private String fatherName;

    @Column(name = "mother_name", length = 100)
    private String motherName;

    @Column(length = 100)
    private String owner;

    @Enumerated(EnumType.STRING)
    @Column(name = "meet_code", nullable = false, length = 10)
    private MeetCode meetCode;

    @Column(name = "rating_1", precision = 10, scale = 2)
    private BigDecimal rating1;

    @Column(name = "rating_2", precision = 10, scale = 2)
    private BigDecimal rating2;

    @Column(name = "rating_3", precision = 10, scale = 2)
    private BigDecimal rating3;

    @Column(name = "rating_4", precision = 10, scale = 2)
    private BigDecimal rating4;

    @Column(name = "coat_color", length = 50)
    private String coatColor;

    @Column(name = "body_type", length = 50)
    private String bodyType;

    @Column(name = "photo_url", length = 500)
    private String photoUrl;

    @Column(name = "thumbnail_url", length = 500)
    private String thumbnailUrl;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
}
