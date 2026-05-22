package com.racepulse.backend.domain.change.entity;

import java.time.LocalDate;
import java.time.OffsetDateTime;

import com.racepulse.backend.domain.horse.entity.Horse;
import com.racepulse.backend.domain.race.entity.Race;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

// =============================================================================
// TrainerChange.java — trainer_changes 테이블 매핑
// =============================================================================
// 조교사 변경은 말, 경주, 이전 조교사, 새 조교사를 함께 봐야 의미가 있습니다.
// @ManyToOne은 "여러 변경 기록이 하나의 말/경주/조교사를 가리킬 수 있다"는 관계를 표현합니다.
// FetchType.LAZY는 실제로 DTO를 만들 때까지 연결 엔티티 조회를 미뤄 불필요한 DB 조회를 줄입니다.
// =============================================================================

@Getter
@Entity
@Table(name = "trainer_changes")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class TrainerChange {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "horse_id", nullable = false)
    private Horse horse;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "race_id")
    private Race race;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "old_trainer_id")
    private TrainerReference oldTrainer;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "new_trainer_id", nullable = false)
    private TrainerReference newTrainer;

    @Column(name = "detected_at", nullable = false)
    private OffsetDateTime detectedAt;

    @Column(name = "change_date", nullable = false)
    private LocalDate changeDate;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "previous_change_id")
    private TrainerChange previousChange;
}
