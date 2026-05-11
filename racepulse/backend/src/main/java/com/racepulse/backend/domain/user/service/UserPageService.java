package com.racepulse.backend.domain.user.service;

import com.racepulse.backend.domain.user.dto.FavoriteRequest;
import com.racepulse.backend.domain.user.dto.FavoriteResponse;
import com.racepulse.backend.domain.user.dto.NotificationSettingResponse;
import com.racepulse.backend.domain.user.dto.PreferenceRequest;
import com.racepulse.backend.domain.user.dto.PreferenceResponse;
import com.racepulse.backend.domain.user.entity.NotificationSetting;
import com.racepulse.backend.domain.user.entity.NotificationType;
import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.repository.NotificationSettingRepository;
import com.racepulse.backend.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class UserPageService {

    private final JdbcTemplate jdbcTemplate;
    private final UserRepository userRepository;
    private final NotificationSettingRepository notificationSettingRepository;

    public List<FavoriteResponse> getFavorites(UUID userId) {
        return jdbcTemplate.query(
                """
                SELECT id, target_type, target_id
                FROM user_favorites
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (rs, rowNum) -> {
                    String targetType = rs.getString("target_type");
                    Long targetId = rs.getLong("target_id");
                    FavoriteTarget target = getFavoriteTarget(targetType, targetId);
                    return FavoriteResponse.builder()
                            .id(rs.getLong("id"))
                            .targetType(targetType)
                            .targetId(targetId)
                            .name(target.name())
                            .subText(target.subText())
                            .build();
                },
                userId
        );
    }

    public FavoriteResponse addFavorite(UUID userId, FavoriteRequest request) {
        String targetType = normalizeTargetType(request.getTargetType());
        jdbcTemplate.update(
                """
                INSERT INTO user_favorites (user_id, target_type, target_id)
                VALUES (?, ?, ?)
                ON CONFLICT (user_id, target_type, target_id) DO NOTHING
                """,
                userId,
                targetType,
                request.getTargetId()
        );
        return getFavorites(userId).stream()
                .filter(item -> item.getTargetType().equals(targetType) && item.getTargetId().equals(request.getTargetId()))
                .findFirst()
                .orElseThrow();
    }

    public void deleteFavorite(UUID userId, Long id) {
        jdbcTemplate.update("DELETE FROM user_favorites WHERE user_id = ? AND id = ?", userId, id);
    }

    public PreferenceResponse getPreferences(UUID userId) {
        List<PreferenceResponse> rows = jdbcTemplate.query(
                """
                SELECT theme, nickname
                FROM user_preferences
                WHERE user_id = ?
                """,
                (rs, rowNum) -> PreferenceResponse.builder()
                        .theme(rs.getString("theme"))
                        .nickname(rs.getString("nickname"))
                        .build(),
                userId
        );
        if (!rows.isEmpty()) {
            return rows.get(0);
        }
        User user = getUser(userId);
        return PreferenceResponse.builder().theme("dark").nickname(user.getNickname()).build();
    }

    public PreferenceResponse updatePreferences(UUID userId, PreferenceRequest request) {
        String theme = request.getTheme() == null ? "dark" : request.getTheme();
        String nickname = request.getNickname() == null ? getUser(userId).getNickname() : request.getNickname();
        jdbcTemplate.update(
                """
                INSERT INTO user_preferences (user_id, theme, nickname, updated_at)
                VALUES (?, ?, ?, now())
                ON CONFLICT (user_id)
                DO UPDATE SET theme = EXCLUDED.theme, nickname = EXCLUDED.nickname, updated_at = now()
                """,
                userId,
                theme,
                nickname
        );
        return PreferenceResponse.builder().theme(theme).nickname(nickname).build();
    }

    @Transactional
    public List<NotificationSettingResponse> getNotifications(UUID userId) {
        User user = getUser(userId);
        for (NotificationType type : NotificationType.values()) {
            notificationSettingRepository.findByUserIdAndType(userId, type)
                    .orElseGet(() -> notificationSettingRepository.save(
                            NotificationSetting.builder().user(user).type(type).enabled(true).build()
                    ));
        }
        return notificationSettingRepository.findByUserId(userId).stream()
                .map(NotificationSettingResponse::from)
                .toList();
    }

    @Transactional
    public NotificationSettingResponse updateNotification(UUID userId, String typeName, boolean enabled) {
        User user = getUser(userId);
        NotificationType type = NotificationType.valueOf(typeName);
        NotificationSetting setting = notificationSettingRepository.findByUserIdAndType(userId, type)
                .orElseGet(() -> notificationSettingRepository.save(
                        NotificationSetting.builder().user(user).type(type).enabled(true).build()
                ));
        setting.updateEnabled(enabled);
        return NotificationSettingResponse.from(setting);
    }

    private FavoriteTarget getFavoriteTarget(String targetType, Long targetId) {
        return switch (targetType) {
            case "HORSE" -> queryTarget("SELECT name, meet_code FROM horses WHERE id = ?", targetId);
            case "JOCKEY" -> queryTarget("SELECT name, meet_code FROM jockeys WHERE id = ?", targetId);
            case "RACE" -> queryTarget("SELECT race_name AS name, rc_date::text AS meet_code FROM races WHERE id = ?", targetId);
            default -> new FavoriteTarget("알 수 없는 항목", targetType);
        };
    }

    private FavoriteTarget queryTarget(String sql, Long targetId) {
        List<FavoriteTarget> rows = jdbcTemplate.query(
                sql,
                (rs, rowNum) -> new FavoriteTarget(rs.getString("name"), rs.getString("meet_code")),
                targetId
        );
        return rows.isEmpty() ? new FavoriteTarget("삭제된 항목", null) : rows.get(0);
    }

    private String normalizeTargetType(String targetType) {
        return targetType == null ? "HORSE" : targetType.toUpperCase(Locale.ROOT);
    }

    private User getUser(UUID userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("사용자 정보를 찾을 수 없습니다."));
    }

    private record FavoriteTarget(String name, String subText) {
    }
}
