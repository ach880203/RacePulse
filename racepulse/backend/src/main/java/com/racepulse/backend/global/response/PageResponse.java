package com.racepulse.backend.global.response;

import java.util.List;

// Page = Spring Data JPA가 "목록 + 전체 개수 + 현재 페이지 정보"를 함께 담아주는 객체입니다.
import org.springframework.data.domain.Page;

// @AllArgsConstructor = 모든 필드를 받는 생성자를 자동 생성합니다.
import lombok.AllArgsConstructor;
// @Builder = 필드 이름을 보면서 객체를 조립할 수 있게 해줍니다.
import lombok.Builder;
// @Getter = 각 필드의 getter 메서드를 자동 생성합니다.
import lombok.Getter;

// =============================================================================
// PageResponse.java — 페이징 목록 응답을 프론트엔드가 쓰기 쉽게 정리한 공통 DTO
// =============================================================================
// 왜 Page를 그대로 내보내지 않았나?
// Spring 내부 구현 세부 정보까지 노출하지 않고,
// 프론트엔드에 꼭 필요한 값만 명확하게 전달하기 위해서입니다.
// =============================================================================

@Getter
@Builder
@AllArgsConstructor
public class PageResponse<T> {

    // 실제 목록 데이터입니다.
    private final List<T> content;

    // 현재 페이지 번호입니다. 첫 페이지는 0입니다.
    private final int page;

    // 한 페이지에 몇 개를 담았는지 나타냅니다.
    private final int size;

    // 전체 데이터 개수입니다.
    private final long totalElements;

    // 전체 페이지 수입니다.
    private final int totalPages;

    // 마지막 페이지인지 여부입니다.
    private final boolean last;

    // Spring의 Page 객체를 우리 프로젝트 공통 형식으로 바꿔주는 변환 메서드입니다.
    public static <T> PageResponse<T> from(Page<T> page) {
        return PageResponse.<T>builder()
                .content(page.getContent())
                .page(page.getNumber())
                .size(page.getSize())
                .totalElements(page.getTotalElements())
                .totalPages(page.getTotalPages())
                .last(page.isLast())
                .build();
    }
}
