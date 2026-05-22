package com.racepulse.backend.infrastructure.redis;

import java.nio.charset.StandardCharsets;

import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.racepulse.backend.domain.change.dto.ChangeEventMessage;
import com.racepulse.backend.domain.change.service.ChangeService;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

// =============================================================================
// ChangeEventSubscriber.java — Redis Pub/Sub 변경 이벤트 구독자
// =============================================================================
// Redis Pub/Sub은 "채널에 문자열 메시지를 발행하면 구독자가 즉시 받는" 구조입니다.
// racepulse:changes 채널 메시지를 JSON으로 해석하고 ChangeService에 넘겨 후속 처리를 맡깁니다.
// =============================================================================

@Slf4j
@Component
@RequiredArgsConstructor
public class ChangeEventSubscriber implements MessageListener {

    private final ObjectMapper objectMapper;
    private final ChangeService changeService;

    @Override
    public void onMessage(Message message, byte[] pattern) {
        String payload = new String(message.getBody(), StandardCharsets.UTF_8);
        try {
            ChangeEventMessage event = objectMapper.readValue(payload, ChangeEventMessage.class);
            log.debug("[Redis 변경 감지] 이벤트 수신. type={}, raceId={}, horseId={}",
                    event.getType(), event.getRaceId(), event.getHorseId());
            changeService.processChangeEvent(event);
        } catch (Exception e) {
            // 잘못된 이벤트 1건 때문에 Redis 리스너가 멈추면 이후 정상 이벤트까지 놓칩니다.
            // 그래서 예외를 밖으로 던지지 않고 로그만 남긴 뒤 다음 메시지를 계속 처리합니다.
            log.warn("[Redis 변경 감지] 이벤트 파싱 실패. payload={}, error={}", payload, e.getMessage());
        }
    }
}
