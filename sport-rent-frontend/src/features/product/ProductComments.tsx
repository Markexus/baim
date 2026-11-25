import { useEffect, useState, type FormEvent } from 'react';

import {
  getProductComments,
  postProductComment,
  type ProductComment,
} from '../../api/productComments.ts';
import { useAuth } from '../auth/authContext.ts';

const URL_PART = /(https?:\/\/[^\s]+)/g;

function CommentBody({ body }: { body: string }) {
  return (
    <p className="mt-2 whitespace-pre-wrap break-words">
      {body.split(URL_PART).map((part, index) =>
        /^https?:\/\//.test(part) ? (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-app-textStrong underline underline-offset-2"
          >
            {part}
          </a>
        ) : (
          part
        )
      )}
    </p>
  );
}

export default function ProductComments({ productSlug }: { productSlug: string }) {
  const { status } = useAuth();
  const [comments, setComments] = useState<ProductComment[]>([]);
  const [body, setBody] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);
    getProductComments(productSlug)
      .then((result) => {
        if (active) setComments(result);
      })
      .catch((failure: unknown) => {
        if (active) setError(failure instanceof Error ? failure.message : 'Błąd komentarzy.');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [productSlug]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!body.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const comment = await postProductComment(productSlug, body.trim());
      setComments((current) => [comment, ...current]);
      setBody('');
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Błąd komentarzy.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="border-t-2 border-app-borderSoft px-4 py-8 text-app-text">
      <h2 className="text-2xl font-semibold">Komentarze</h2>
      {status === 'authenticated' && (
        <form onSubmit={(event) => void submit(event)} className="mt-5 max-w-2xl">
          <label htmlFor="product-comment" className="block font-medium">
            Dodaj komentarz
          </label>
          <textarea
            id="product-comment"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            maxLength={1000}
            required
            rows={3}
            className="mt-2 w-full rounded-lg border border-app-borderSoft bg-app-surface p-3 outline-none"
          />
          <button
            type="submit"
            disabled={isSubmitting || !body.trim()}
            className="mt-2 rounded-lg bg-app-surfaceStrong px-5 py-2 font-semibold text-app-textInverted disabled:opacity-50"
          >
            {isSubmitting ? 'Dodawanie…' : 'Dodaj komentarz'}
          </button>
        </form>
      )}
      {error && <p role="alert" className="mt-4 text-app-danger">{error}</p>}
      {isLoading ? (
        <p className="mt-5 text-app-textMuted">Ładowanie komentarzy…</p>
      ) : comments.length === 0 ? (
        <p className="mt-5 text-app-textMuted">Brak komentarzy.</p>
      ) : (
        <ul className="mt-6 space-y-4">
          {comments.map((comment) => (
            <li key={comment.id} className="rounded-xl border border-app-borderSoft bg-app-surfaceSoft p-4">
              <div className="flex flex-wrap items-baseline gap-x-3">
                <strong>{comment.author_name}</strong>
                <time className="text-sm text-app-textMuted" dateTime={comment.created_at}>
                  {new Date(comment.created_at).toLocaleDateString('pl-PL')}
                </time>
              </div>
              <CommentBody body={comment.body} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
