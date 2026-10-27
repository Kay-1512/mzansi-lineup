import { client } from "./client";

export async function getSources() {
  const { data } = await client.get("/sources/");
  return data;
}

export async function getGenres() {
  const { data } = await client.get("/genres/");
  return data;
}

export async function getOnboardingSources() {
  const { data } = await client.get("/onboarding/sources/");
  return data.sources;
}

export async function setOnboardingSources(sourceSlugs) {
  const { data } = await client.put("/onboarding/sources/", { sources: sourceSlugs });
  return data.sources;
}

export async function getOnboardingGenres() {
  const { data } = await client.get("/onboarding/genres/");
  return data;
}

export async function setOnboardingGenres(genreSlugs, internationalActs) {
  const { data } = await client.put("/onboarding/genres/", {
    genres: genreSlugs,
    international_acts: internationalActs,
  });
  return data;
}

export async function getWatchedArtists() {
  const { data } = await client.get("/artists/");
  return data;
}

export async function addWatchedArtist(name, externalId, imageUrl) {
  const { data } = await client.post("/artists/", {
    name,
    external_id: externalId || null,
    image_url: imageUrl || "",
  });
  return data;
}

export async function removeWatchedArtist(id) {
  await client.delete(`/artists/${id}/`);
}

export async function searchArtists(query) {
  const { data } = await client.get("/artists/search/", { params: { q: query } });
  return data.results;
}

export async function getWatchedInstagramPages() {
  const { data } = await client.get("/instagram-pages/");
  return data;
}

export async function addWatchedInstagramPage(handle, feedUrl) {
  const { data } = await client.post("/instagram-pages/", {
    handle,
    feed_url: feedUrl,
  });
  return data;
}

export async function removeWatchedInstagramPage(id) {
  await client.delete(`/instagram-pages/${id}/`);
}
