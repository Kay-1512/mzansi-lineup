import { useEffect, useState } from "react";
import {
  addWatchedInstagramPage,
  getWatchedInstagramPages,
  removeWatchedInstagramPage,
} from "../api/catalog";

// Unlike ArtistSearchPicker, there's no API to search against here —
// Instagram won't hand out another page's data, so the user supplies both
// the handle (just a label) and an RSS feed URL from a third-party
// Instagram-to-RSS proxy they've already set up (see README "Getting API
// keys" → Instagram). This just manages the add/remove list.
export default function InstagramPagePicker() {
  const [pages, setPages] = useState([]);
  const [handle, setHandle] = useState("");
  const [feedUrl, setFeedUrl] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getWatchedInstagramPages().then(setPages);
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    if (!handle.trim() || !feedUrl.trim()) return;

    setSubmitting(true);
    setError("");
    try {
      const created = await addWatchedInstagramPage(handle.trim(), feedUrl.trim());
      setPages((prev) => [...prev, created]);
      setHandle("");
      setFeedUrl("");
    } catch (err) {
      const data = err.response?.data || {};
      const firstError = Object.values(data)[0];
      setError((Array.isArray(firstError) ? firstError[0] : firstError) || "Couldn't add that page.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRemove(id) {
    await removeWatchedInstagramPage(id);
    setPages((prev) => prev.filter((p) => p.id !== id));
  }

  return (
    <>
      <form className="instagram-page-form" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="Handle, e.g. milkandcookies"
          value={handle}
          onChange={(e) => setHandle(e.target.value)}
        />
        <input
          type="url"
          placeholder="RSS feed URL (rss.app, Bazaar, ...)"
          value={feedUrl}
          onChange={(e) => setFeedUrl(e.target.value)}
        />
        <button type="submit" disabled={submitting}>
          Add
        </button>
      </form>
      {error && <p className="form-error">{error}</p>}

      {pages.length > 0 && (
        <ul className="instagram-page-list">
          {pages.map((page) => (
            <li key={page.id}>
              <span>@{page.handle}</span>
              <button type="button" className="btn-ghost" onClick={() => handleRemove(page.id)}>
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
