import { apiGet, apiPost, type CourseDetail, type ExamResponse, type QuestionOut } from '@/lib/api';
import type { Curso } from '@/types';

export type ContentBlockKind = 'video' | 'pdf' | 'imagen' | 'audio' | 'texto';

export interface ContentBlockProgress {
  video_last_pos_seconds: number;
  video_max_seen_pct: number;
  pdf_last_page: number;
  pdf_total_pages: number | null;
  completed: boolean;
}

export interface ContentBlockView {
  id: string;
  kind: ContentBlockKind;
  media_key: string | null;
  content_body: string | null;
  duration_seconds: number | null;
  order_index: number;
  progress: ContentBlockProgress;
}

export interface PlayTokenByBlockRequest {
  block_id: string;
}

export interface PlayTokenByBlockResponse {
  token: string;
  media_url: string;
  expires_in: number;
}

export interface BlockHeartbeatRequest {
  type: ContentBlockKind;
  block_id: string;
  pos_seconds?: number;
  duration_seconds?: number;
  max_seen_pct?: number;
  last_page?: number;
  total_pages?: number;
}

export interface BlockHeartbeatResponse {
  state: string;
  video_last_pos_seconds: number;
  video_max_seen_pct: number;
  pdf_last_page: number;
  pdf_total_pages: number | null;
}

export const coursesService = {
  async getAll(): Promise<Curso[]> {
    return apiGet('/api/v1/courses' as any) as Promise<Curso[]>;
  },

  async getBySlug(slug: string): Promise<CourseDetail> {
    return apiGet(`/api/v1/courses/{slug}` as any, { params: { slug } }) as Promise<CourseDetail>;
  },

  async enroll(slug: string): Promise<any> {
    return apiPost(`/api/v1/courses/{slug}/enroll` as any, { params: { slug } });
  },

  async getTopic(topicId: string): Promise<any> {
    return apiGet(`/api/v1/topics/{topic_id}` as any, { params: { topic_id: topicId } });
  },

  async getTopicExam(topicId: string): Promise<ExamResponse> {
    return apiGet(`/api/v1/topics/{topic_id}/exam` as any, { params: { topic_id: topicId } }) as Promise<ExamResponse>;
  },

  async submitTopicExam(topicId: string, payload: any) {
    return apiPost(`/api/v1/topics/{topic_id}/exam/submit` as any, { params: { topic_id: topicId }, body: payload });
  },
};
