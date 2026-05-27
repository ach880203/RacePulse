package com.racepulse.backend.domain.jockey.service;

import com.racepulse.backend.domain.jockey.dto.JockeyResponse;
import com.racepulse.backend.domain.jockey.entity.Jockey;
import com.racepulse.backend.domain.jockey.repository.JockeyRepository;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class JockeyService {

    private final JockeyRepository jockeyRepository;

    public Page<JockeyResponse> getJockeys(String meetCode, String name, Pageable pageable) {
        Specification<Jockey> spec = (root, query, cb) -> cb.conjunction();

        if (meetCode != null && !meetCode.isBlank()) {
            spec = spec.and((root, query, cb) -> cb.equal(root.get("meetCode"), meetCode));
        }

        if (name != null && !name.isBlank()) {
            String keyword = "%" + name.trim().toLowerCase() + "%";
            spec = spec.and((root, query, cb) ->
                    cb.like(cb.lower(root.get("name")), keyword));
        }

        return jockeyRepository.findAll(spec, pageable).map(JockeyResponse::from);
    }

    public JockeyResponse getJockey(Long id) {
        return jockeyRepository.findById(id)
                .map(JockeyResponse::from)
                .orElseThrow(() -> new BusinessException(ErrorCode.JOCKEY_NOT_FOUND));
    }
}
