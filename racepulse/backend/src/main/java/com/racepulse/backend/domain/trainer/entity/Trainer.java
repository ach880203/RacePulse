package com.racepulse.backend.domain.trainer.entity;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Entity
@Table(name = "trainers")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Trainer {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // V8 마이그레이션에서 trainer_code → license_no 로 컬럼명 변경됨
    @Column(name = "license_no", length = 20)
    private String licenseNo;

    @Column(name = "meet_code", nullable = false, length = 10)
    private String meetCode;

    @Column(nullable = false, length = 50)
    private String name;

    @Column(name = "eng_name", length = 100)
    private String engName;

    @Column(name = "birth_year")
    private Integer birthYear;

    @Column(name = "debut_year")
    private Integer debutYear;

    @Column(length = 10)
    private String affiliation;

    @Column(name = "photo_url")
    private String photoUrl;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive;

    // V8 마이그레이션에서 추가된 성적 집계 컬럼들
    @Column(name = "win_rate_total", precision = 5, scale = 4)
    private BigDecimal winRateTotal;

    @Column(name = "win_rate_recent", precision = 5, scale = 4)
    private BigDecimal winRateRecent;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
}
