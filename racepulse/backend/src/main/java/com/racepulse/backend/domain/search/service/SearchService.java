package com.racepulse.backend.domain.search.service;

import com.racepulse.backend.domain.search.dto.SearchItemResponse;
import com.racepulse.backend.domain.search.dto.SearchResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Locale;

@Service
@RequiredArgsConstructor
public class SearchService {

    private final JdbcTemplate jdbcTemplate;

    public SearchResponse search(String query, String type) {
        String safeQuery = query == null ? "" : query.trim();
        String safeType = type == null ? "ALL" : type.toUpperCase(Locale.ROOT);
        String likeQuery = "%" + safeQuery + "%";

        return SearchResponse.builder()
                .query(safeQuery)
                .horses(shouldSearch(safeType, "HORSE") ? searchHorses(likeQuery) : List.of())
                .jockeys(shouldSearch(safeType, "JOCKEY") ? searchJockeys(likeQuery) : List.of())
                .trainers(shouldSearch(safeType, "TRAINER") ? searchTrainers(likeQuery) : List.of())
                .races(shouldSearch(safeType, "RACE") ? searchRaces(likeQuery) : List.of())
                .build();
    }

    private boolean shouldSearch(String type, String targetType) {
        return "ALL".equals(type) || targetType.equals(type);
    }

    private List<SearchItemResponse> searchHorses(String likeQuery) {
        return jdbcTemplate.query(
                """
                SELECT id, name, meet_code, thumbnail_url
                FROM horses
                WHERE name ILIKE ?
                ORDER BY name ASC
                LIMIT 8
                """,
                (rs, rowNum) -> SearchItemResponse.builder()
                        .id(rs.getLong("id"))
                        .name(rs.getString("name"))
                        .subText(rs.getString("meet_code"))
                        .thumbnailUrl(rs.getString("thumbnail_url"))
                        .build(),
                likeQuery
        );
    }

    private List<SearchItemResponse> searchJockeys(String likeQuery) {
        return jdbcTemplate.query(
                """
                SELECT id, name, meet_code
                FROM jockeys
                WHERE name ILIKE ?
                ORDER BY name ASC
                LIMIT 8
                """,
                (rs, rowNum) -> SearchItemResponse.builder()
                        .id(rs.getLong("id"))
                        .name(rs.getString("name"))
                        .subText(rs.getString("meet_code"))
                        .thumbnailUrl(null)
                        .build(),
                likeQuery
        );
    }

    private List<SearchItemResponse> searchTrainers(String likeQuery) {
        return jdbcTemplate.query(
                """
                SELECT id, name, meet_code
                FROM trainers
                WHERE name ILIKE ?
                ORDER BY name ASC
                LIMIT 8
                """,
                (rs, rowNum) -> SearchItemResponse.builder()
                        .id(rs.getLong("id"))
                        .name(rs.getString("name"))
                        .subText(rs.getString("meet_code"))
                        .thumbnailUrl(null)
                        .build(),
                likeQuery
        );
    }

    private List<SearchItemResponse> searchRaces(String likeQuery) {
        return jdbcTemplate.query(
                """
                SELECT id, race_name, rc_date, race_no
                FROM races
                WHERE race_name ILIKE ?
                ORDER BY rc_date DESC, race_no ASC
                LIMIT 8
                """,
                (rs, rowNum) -> SearchItemResponse.builder()
                        .id(rs.getLong("id"))
                        .name(rs.getString("race_name"))
                        .subText(rs.getDate("rc_date") + " · " + rs.getInt("race_no") + "경주")
                        .thumbnailUrl(null)
                        .build(),
                likeQuery
        );
    }
}
