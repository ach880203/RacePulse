package com.racepulse.backend.infrastructure.redis;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.RedisMessageListenerContainer;

// =============================================================================
// ChangeRedisConfig.java — 변경 감지 Redis 채널 연결 설정
// =============================================================================
// RedisMessageListenerContainer는 Redis 연결을 열어 두고 지정된 채널 메시지를 기다리는 Spring 컴포넌트입니다.
// racepulse:changes 채널에 메시지가 발행되면 ChangeEventSubscriber.onMessage가 호출됩니다.
// =============================================================================

@Configuration
public class ChangeRedisConfig {

    public static final String CHANGE_CHANNEL = "racepulse:changes";

    @Bean
    public RedisMessageListenerContainer changeRedisMessageListenerContainer(
            RedisConnectionFactory connectionFactory,
            ChangeEventSubscriber changeEventSubscriber
    ) {
        RedisMessageListenerContainer container = new RedisMessageListenerContainer();
        container.setConnectionFactory(connectionFactory);
        container.addMessageListener(changeEventSubscriber, new ChannelTopic(CHANGE_CHANNEL));
        return container;
    }
}
