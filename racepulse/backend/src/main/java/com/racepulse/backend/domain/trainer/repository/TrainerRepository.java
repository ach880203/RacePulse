package com.racepulse.backend.domain.trainer.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import com.racepulse.backend.domain.trainer.entity.Trainer;

public interface TrainerRepository extends JpaRepository<Trainer, Long>, JpaSpecificationExecutor<Trainer> {
}
