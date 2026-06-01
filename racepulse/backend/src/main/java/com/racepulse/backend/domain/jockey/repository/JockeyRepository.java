package com.racepulse.backend.domain.jockey.repository;

import com.racepulse.backend.domain.jockey.entity.Jockey;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

@Repository
public interface JockeyRepository extends JpaRepository<Jockey, Long>, JpaSpecificationExecutor<Jockey> {
}
