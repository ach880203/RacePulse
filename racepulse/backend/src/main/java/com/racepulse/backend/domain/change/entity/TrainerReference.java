package com.racepulse.backend.domain.change.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

// =============================================================================
// TrainerReference.java — trainer_changes가 참조하는 조교사 최소 엔티티
// =============================================================================
// 현재 조교사 전용 도메인 엔티티가 없으므로 변경 감지 API에서 필요한 최소 컬럼만 매핑합니다.
// JPA는 엔티티에 없는 DB 컬럼을 무시하므로 trainers 테이블 전체를 모두 적을 필요는 없습니다.
// =============================================================================

@Getter
@Entity
@Table(name = "trainers")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class TrainerReference {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String name;
}
