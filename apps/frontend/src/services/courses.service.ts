import { apiGet, apiPost, type CourseDetail, type ExamResponse, type QuestionOut } from '@/lib/api';
import type { Curso } from '@/types';

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
    return apiPost(`/api/v1/topics/{topic_id}/exam` as any, { params: { topic_id: topicId } }) as Promise<ExamResponse>;
  },

  async submitTopicExam(topicId: string, payload: any) {
    return apiPost(`/api/v1/topics/{topic_id}/exam/submit` as any, { params: { topic_id: topicId }, body: payload });
  },
};
