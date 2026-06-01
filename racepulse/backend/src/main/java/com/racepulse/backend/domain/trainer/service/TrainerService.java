package com.racepulse.backend.domain.trainer.service;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.racepulse.backend.domain.trainer.dto.TrainerResponse;
import com.racepulse.backend.domain.trainer.entity.Trainer;
import com.racepulse.backend.domain.trainer.repository.TrainerRepository;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TrainerService {

    private final TrainerRepository trainerRepository;

    public Page<TrainerResponse> getTrainers(String meetCode, String name, Pageable pageable) {
        Specification<Trainer> specification = (root, query, criteriaBuilder) -> criteriaBuilder.conjunction();

        if (meetCode != null && !meetCode.isBlank()) {
            specification = specification.and((root, query, criteriaBuilder) ->
                    criteriaBuilder.equal(root.get("meetCode"), meetCode));
        }

        if (name != null && !name.isBlank()) {
            String keyword = "%" + name.trim().toLowerCase() + "%";
            specification = specification.and((root, query, criteriaBuilder) ->
                    criteriaBuilder.like(criteriaBuilder.lower(root.get("name")), keyword));
        }

        return trainerRepository.findAll(specification, pageable)
                .map(TrainerResponse::from);
    }

    public TrainerResponse getTrainerById(Long trainerId) {
        Trainer trainer = trainerRepository.findById(trainerId)
                .orElseThrow(() -> new BusinessException(ErrorCode.TRAINER_NOT_FOUND));
        return TrainerResponse.from(trainer);
    }
}
