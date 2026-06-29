import { apiPost } from '@/lib/api';

// ---------------------------------------------------------------------------
// ffmpeg.wasm faststart optimization
// ---------------------------------------------------------------------------
// Lazy-loaded: only imported when a video upload is triggered.
// Applies -movflags faststart (moves moov atom to front of file) so the
// browser can begin HTTP Range Request streaming immediately without a full
// download. This is a copy-only operation — NO re-encoding, NO quality loss.
// ---------------------------------------------------------------------------

let ffmpegInstance: import('@ffmpeg/ffmpeg').FFmpeg | null = null;

async function getFFmpeg() {
  if (!ffmpegInstance) {
    const { FFmpeg } = await import('@ffmpeg/ffmpeg');
    ffmpegInstance = new FFmpeg();
  }
  return ffmpegInstance;
}

/**
 * Reorder MP4/MOV metadata (moov atom) to the start of the file using ffmpeg.wasm.
 * This enables HTTP Range Request streaming (progressive download) from R2.
 *
 * - Only works on MP4/MOV files with H.264+AAC (compatible containers).
 * - Falls back to original file if ffmpeg fails or browser lacks WASM support.
 * - Average processing time: 200–800ms for a 200MB file (no re-encoding).
 */
export async function optimizeVideoForStreaming(
  file: File,
  onProgress?: (phase: 'loading' | 'optimizing' | 'done') => void,
): Promise<Blob> {
  // Validate: only optimize MP4/MOV files. AVI/MKV etc. would need transcoding.
  const compatibleTypes = new Set(['video/mp4', 'video/quicktime', 'video/x-m4v']);
  if (!compatibleTypes.has(file.type)) {
    console.warn(`[media] Skipping faststart: unsupported type ${file.type}`);
    return file;
  }

  try {
    onProgress?.('loading');
    const { fetchFile } = await import('@ffmpeg/util');
    const ffmpeg = await getFFmpeg();

    if (!ffmpeg.loaded) {
      // Load ffmpeg core from CDN (cached by browser after first load)
      // Single-thread core (no SharedArrayBuffer needed).
      // COEP headers were removed from vite.config.ts — R2 presigned PUT uploads
      // require cross-origin fetch which COEP was blocking.
      await ffmpeg.load({
        coreURL: 'https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm/ffmpeg-core.js',
        wasmURL: 'https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm/ffmpeg-core.wasm',
      });
    }

    onProgress?.('optimizing');
    const inputName = 'input.mp4';
    const outputName = 'output.mp4';

    await ffmpeg.writeFile(inputName, await fetchFile(file));

    // -c copy = no re-encoding, just container reorder
    // -movflags faststart = move moov atom to front
    await ffmpeg.exec(['-i', inputName, '-c', 'copy', '-movflags', 'faststart', outputName]);

    const data = await ffmpeg.readFile(outputName);
    const optimizedBlob = new Blob([data as any], { type: 'video/mp4' });

    // Cleanup WASM virtual filesystem
    await ffmpeg.deleteFile(inputName);
    await ffmpeg.deleteFile(outputName);

    onProgress?.('done');
    console.log(
      `[media] faststart applied: ${(file.size / 1024 / 1024).toFixed(1)}MB → ${(optimizedBlob.size / 1024 / 1024).toFixed(1)}MB`,
    );
    return optimizedBlob;
  } catch (err) {
    // Non-fatal: fall back to original file. Streaming will still work,
    // just with a slight delay while the browser finds the moov atom.
    console.warn('[media] faststart optimization failed, uploading original:', err);
    return file;
  }
}

// ---------------------------------------------------------------------------
// Upload service
// ---------------------------------------------------------------------------

export const mediaService = {
  /**
   * Optimize (if video) and upload a file directly to Cloudflare R2.
   *
   * @param file     The file object from input.
   * @param scope    The scope of the file ('video' | 'pdf' | 'imagen' | 'cover').
   * @param onPhase  Optional callback to track upload phases for progress UI.
   * @returns        The generated media key to save in the database.
   */
  async uploadFile(
    file: File,
    scope: 'video' | 'pdf' | 'imagen' | 'cover',
    onPhase?: (phase: 'optimizing' | 'uploading' | 'done') => void,
  ): Promise<string> {
    // 1. For video files: apply faststart optimization before upload
    let fileToUpload: File | Blob = file;
    if (scope === 'video') {
      onPhase?.('optimizing');
      fileToUpload = await optimizeVideoForStreaming(file, (p) => {
        if (p === 'done') onPhase?.('uploading');
      });
    } else {
      onPhase?.('uploading');
    }

    // 2. Get presigned upload URL from backend
    const response = (await apiPost('/api/v1/media/upload-url' as any, {
      body: {
        filename: file.name,
        content_type: file.type,
        scope,
      },
    })) as { put_url: string; key: string };

    // 3. Direct PUT request to R2 via presigned URL
    const uploadResponse = await fetch(response.put_url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type,
      },
      body: fileToUpload,
    });

    if (!uploadResponse.ok) {
      throw new Error(`Failed to upload file to storage: ${uploadResponse.statusText}`);
    }

    onPhase?.('done');

    // 4. Return the storage key
    return response.key;
  },
};
