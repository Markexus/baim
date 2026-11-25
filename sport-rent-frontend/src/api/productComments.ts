import { getAccessToken, refreshAccessToken } from './authSession.ts';

export type ProductComment = {
  id: number;
  author_name: string;
  body: string;
  created_at: string;
};

const commentsUrl = (slug: string) =>
  `${import.meta.env.VITE_API_URL}/product/${encodeURIComponent(slug)}/comments`;

export async function getProductComments(slug: string): Promise<ProductComment[]> {
  const response = await fetch(commentsUrl(slug));
  if (!response.ok) throw new Error('Nie udało się pobrać komentarzy.');
  return (await response.json()) as ProductComment[];
}

export async function postProductComment(slug: string, body: string): Promise<ProductComment> {
  const token = getAccessToken();
  if (!token) throw new Error('Zaloguj się, aby dodać komentarz.');

  const submit = (accessToken: string) =>
    fetch(commentsUrl(slug), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ body }),
    });

  let response = await submit(token);
  if (response.status === 401) {
    const freshToken = await refreshAccessToken();
    if (freshToken) response = await submit(freshToken);
  }
  if (!response.ok) throw new Error('Nie udało się dodać komentarza.');
  return (await response.json()) as ProductComment;
}
