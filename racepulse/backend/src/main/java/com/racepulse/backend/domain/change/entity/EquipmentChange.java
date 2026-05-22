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
// EquipmentChange.java — equipment_changes 테이블 매핑
// =============================================================================
// 장비 변경은 "무엇이 무엇으로 바뀌었는지"가 핵심이므로 oldValue/newValue를 그대로 노출합니다.
// blinkerFirstTime은 블링커 첫 착용처럼 예측에 영향을 줄 수 있는 특수 신호를 분리한 값입니다.
// =============================================================================

@Getter
@Entity
@Table(name = "equipment_changes")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class EquipmentChange {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "horse_id", nullable = false)
    private Horse horse;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "race_id")
    private Race race;

    @Column(name = "equipment_type", nullable = false, length = 20)
    private String equipmentType;

    @Column(name = "old_value", length = 50)
    private String oldValue;

    @Column(name = "new_value", nullable = false, length = 50)
    private String newValue;

    @Column(name = "detected_at", nullable = false)
    private OffsetDateTime detectedAt;

    @Column(name = "change_date", nullable = false)
    private LocalDate changeDate;

    @Column(name = "blinker_first_time", nullable = false)
    private boolean blinkerFirstTime;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "previous_change_id")
    private EquipmentChange previousChange;
}
