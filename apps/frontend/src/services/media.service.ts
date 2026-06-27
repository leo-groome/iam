import { apiPost } from '@/lib/api';

export const mediaService = {
  /**
   * Request a presigned URL and upload a file directly to Cloudflare R2.
   * 
   * @param file The file object from input.
   * @param scope The scope of the file ('video' | 'pdf' | 'imagen' | 'cover').
   * @returns The generated media key to save in the database.
   */
  async uploadFile(
    file: File,
    scope: 'video' | 'pdf' | 'imagen' | 'cover'
  ): Promise<string> {
    // 1. Get presigned upload URL from backend
    const response = (await apiPost('/api/v1/media/upload-url' as any, {
      body: {
        filename: file.name,
        content_type: file.type,
        scope,
      },
    })) as { put_url: string; key: string };

    // 2. Direct PUT request to R2 via presigned URL
    const uploadResponse = await fetch(response.put_url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
      },
      body: file,
    });

    if (!uploadResponse.ok) {
      throw new Error(`Failed to upload file to storage: ${uploadResponse.statusText}`);
    }

    // 3. Return the storage key
    return response.key;
  },
};
