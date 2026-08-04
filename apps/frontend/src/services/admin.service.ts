import { apiBlob, apiGet, apiPost, apiPatch, apiPut, apiDelete } from '@/lib/api';

export type BlockKind = 'video' | 'pdf' | 'imagen' | 'audio' | 'texto';

/** Content block as returned by the backend (GET topic detail). */
export interface ContentBlockOut {
  id: string;
  kind: BlockKind;
  media_key: string | null;
  content_body: string | null;
  duration_seconds: number | null;
  order_index: number;
}

/** Content block payload sent to PUT /admin/topics/{id}/blocks. */
export interface ContentBlockIn {
  kind: BlockKind;
  media_key: string | null;
  content_body: string | null;
  duration_seconds: number | null;
  order_index: number;
}

export const adminService = {
  // Dashboard
  async getDashboardKpis(): Promise<any> {
    return apiGet('/api/v1/admin/dashboard' as any) as Promise<any>;
  },

  // Courses
  async getCourses(): Promise<any> {
    return apiGet('/api/v1/admin/courses' as any) as Promise<any>;
  },

  async getCourse(id: string): Promise<any> {
    return apiGet('/api/v1/admin/courses/{id}' as any, { params: { id } }) as Promise<any>;
  },

  async createCourse(data: any): Promise<any> {
    return apiPost('/api/v1/admin/courses' as any, { body: data }) as Promise<any>;
  },

  async updateCourse(id: string, data: any): Promise<any> {
    return apiPatch('/api/v1/admin/courses/{id}' as any, { params: { id }, body: data }) as Promise<any>;
  },

  async publishCourse(id: string): Promise<any> {
    return apiPost('/api/v1/admin/courses/{id}/publish' as any, { params: { id } }) as Promise<any>;
  },

  async archiveCourse(id: string): Promise<any> {
    return apiPost('/api/v1/admin/courses/{id}/archive' as any, { params: { id } }) as Promise<any>;
  },

  async deleteCourse(id: string, confirmationTitle: string): Promise<any> {
    return apiDelete('/api/v1/admin/courses/{id}' as any, {
      params: { id },
      query: { confirmation_title: confirmationTitle },
    }) as Promise<any>;
  },

  // Modules
  async createModule(courseId: string, data: any): Promise<any> {
    return apiPost('/api/v1/admin/courses/{course_id}/modules' as any, {
      params: { course_id: courseId },
      body: data,
    }) as Promise<any>;
  },

  async updateModule(id: string, data: any): Promise<any> {
    return apiPatch('/api/v1/admin/modules/{id}' as any, { params: { id }, body: data }) as Promise<any>;
  },

  async deleteModule(id: string): Promise<any> {
    return apiDelete('/api/v1/admin/modules/{id}' as any, { params: { id } }) as Promise<any>;
  },

  async reorderModules(courseId: string, order: string[]): Promise<any> {
    return apiPost('/api/v1/admin/modules/reorder' as any, {
      body: { course_id: courseId, order },
    }) as Promise<any>;
  },

  // Topics
  async createTopic(moduleId: string, data: any): Promise<any> {
    return apiPost('/api/v1/admin/modules/{module_id}/topics' as any, {
      params: { module_id: moduleId },
      body: data,
    }) as Promise<any>;
  },

  async updateTopic(id: string, data: any): Promise<any> {
    return apiPatch('/api/v1/admin/topics/{id}' as any, { params: { id }, body: data }) as Promise<any>;
  },

  async getTopicDetail(id: string): Promise<any> {
    return apiGet('/api/v1/admin/topics/{id}' as any, { params: { id } }) as Promise<any>;
  },

  async deleteTopic(id: string): Promise<any> {
    return apiDelete('/api/v1/admin/topics/{id}' as any, { params: { id } }) as Promise<any>;
  },

  async reorderTopics(moduleId: string, order: string[]): Promise<any> {
    return apiPost('/api/v1/admin/topics/reorder' as any, {
      body: { module_id: moduleId, order },
    }) as Promise<any>;
  },

  // Questions
  async createQuestion(topicId: string, data: any): Promise<any> {
    return apiPost('/api/v1/admin/topics/{topic_id}/questions' as any, {
      params: { topic_id: topicId },
      body: data,
    }) as Promise<any>;
  },

  async listModuleQuestions(moduleId: string): Promise<any> {
    return apiGet('/api/v1/admin/modules/{module_id}/questions' as any, {
      params: { module_id: moduleId },
    }) as Promise<any>;
  },

  async createModuleQuestion(moduleId: string, data: any): Promise<any> {
    return apiPost('/api/v1/admin/modules/{module_id}/questions' as any, {
      params: { module_id: moduleId },
      body: data,
    }) as Promise<any>;
  },

  async updateQuestion(id: string, enunciado: string): Promise<any> {
    return apiPatch('/api/v1/admin/questions/{id}' as any, {
      params: { id },
      body: { enunciado },
    }) as Promise<any>;
  },

  async archiveQuestion(id: string): Promise<any> {
    return apiDelete('/api/v1/admin/questions/{id}' as any, { params: { id } }) as Promise<any>;
  },

  async replaceTopicQuestions(topicId: string, questions: any[]): Promise<any> {
    return apiPost('/api/v1/admin/topics/{topic_id}/questions/bulk' as any, {
      params: { topic_id: topicId },
      body: questions,
    }) as Promise<any>;
  },

  async replaceTopicBlocks(topicId: string, blocks: ContentBlockIn[]): Promise<any> {
    return apiPut('/api/v1/admin/topics/{topic_id}/blocks' as any, {
      params: { topic_id: topicId },
      body: blocks,
    }) as Promise<any>;
  },

  // Options
  async updateOption(id: string, data: any): Promise<any> {
    return apiPatch('/api/v1/admin/options/{id}' as any, { params: { id }, body: data }) as Promise<any>;
  },

  // Students
  async getStudents(params?: { q?: string; status?: string; page?: number }): Promise<any> {
    return apiGet('/api/v1/admin/students' as any, { query: params }) as Promise<any>;
  },

  async getStudentDetail(id: string): Promise<any> {
    return apiGet('/api/v1/admin/students/{id}' as any, { params: { id } }) as Promise<any>;
  },

  // Reports
  async getTopicPassRate(courseId: string): Promise<any> {
    return apiGet('/api/v1/admin/reports/topic-pass-rate' as any, { query: { course_id: courseId } }) as Promise<any>;
  },

  async exportReport(type: string): Promise<{ blob: Blob; filename: string | null }> {
    return apiBlob('/api/v1/admin/reports/export' as any, { query: { type } });
  },
};
