function formatPostedAt(isoString) {
  if (!isoString) return "";
  return new Date(isoString).toLocaleString("en-ZA", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function InstagramPostCard({ post }) {
  return (
    <div className="instagram-post-card">
      {post.image_url && (
        <img src={post.image_url} alt="" className="instagram-post-image" />
      )}
      <div className="instagram-post-body">
        <p className="instagram-post-handle">@{post.handle}</p>
        {post.caption && <p className="instagram-post-caption">{post.caption}</p>}
        <div className="instagram-post-meta">
          <span>{formatPostedAt(post.posted_at)}</span>
          {post.post_url && (
            <a href={post.post_url} target="_blank" rel="noreferrer" className="btn-link">
              View post
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
