import { apiGet, apiPost, type CourseDetail, type ExamResponse, type QuestionOut } from '@/lib/api';
import type { Curso } from '@/types';

export const coursesService = {
  async getAll(): Promise<Curso[]> {
    return apiGet('/courses' as any) as Promise<Curso[]>;
  },

  async getBySlug(slug: string): Promise<CourseDetail> {
    return apiGet(`/courses/{slug}` as any, { params: { slug } }) as Promise<CourseDetail>;
  },

  async getTopicExam(topicId: string): Promise<ExamResponse> {
    return apiPost(`/topics/{topic_id}/exam` as any, { params: { topic_id: topicId } }) as Promise<ExamResponse>;
  },

  async submitTopicExam(topicId: string, payload: any) {
    return apiPost(`/topics/{topic_id}/exam/submit` as any, { params: { topic_id: topicId }, body: payload });
  },
};
