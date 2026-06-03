import type { HttpClient } from '@substack-api/internal/http-client'

export type FollowingUser = {
  id: number
  handle?: string
}
/**
 * Service responsible for following-related HTTP operations
 * Returns internal types that can be transformed into domain models
 */
export class FollowingService {
  constructor(
    private readonly publicationClient: HttpClient,
    private readonly substackClient: HttpClient
  ) {}

  /**
   * Get users that the authenticated user follows.
   *
   * Uses the reader feed endpoint on the substack.com host, which is
   * cookie-authenticated and returns a flat array of user ids. This replaces
   * the old `/user-setting` + publication-host `/subscriber-lists` path, both
   * of which broke in 2026: `/user-setting` now rejects `type:last_home_tab`
   * (400) and the publication host gates `/subscriber-lists` behind a
   * Cloudflare challenge (403). The flat-id list carries no handles, so
   * callers resolve each profile via `ProfileService.getProfileById`.
   *
   * @returns Promise<FollowingUser[]> - Array of followed user ids
   * @throws {Error} When following list cannot be retrieved
   */
  async getFollowing(): Promise<FollowingUser[]> {
    const data = await this.substackClient.get<unknown>('/feed/following?limit=500')
    if (!Array.isArray(data)) {
      throw new Error(
        `Unexpected /feed/following response: expected an array of ids, got ${typeof data}`
      )
    }
    return data
      .map((id) => Number(id))
      .filter((id) => Number.isFinite(id))
      .map((id) => ({ id }))
  }
}
