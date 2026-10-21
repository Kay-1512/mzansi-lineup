import { useState } from "react";

export default function ArtistCard({ name, imageUrl, selected, onClick }) {
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <button
      type="button"
      className={`artist-card ${selected ? "artist-card-selected" : ""}`}
      onClick={onClick}
    >
      <span className="artist-card-image">
        {imageUrl && !imageFailed ? (
          <img src={imageUrl} alt="" onError={() => setImageFailed(true)} />
        ) : (
          <span className="artist-card-initial">{name.charAt(0)}</span>
        )}
        {selected && <span className="artist-card-check">✓</span>}
      </span>
      <span className="artist-card-name">{name}</span>
    </button>
  );
}
