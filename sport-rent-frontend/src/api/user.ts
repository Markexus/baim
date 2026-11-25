import type { PersonalData } from '../features/profile/account/PersonalDataForm.tsx';
import { getCsrfHeaders } from './authSession.ts';
import { api } from './client.ts';

export const getUser = () => api.GET('/user');

export async function updateAccountEmail(email: string): Promise<void> {
  const headers = new Headers(getCsrfHeaders());
  headers.set('Content-Type', 'application/x-www-form-urlencoded');
  const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/account/email`, {
    method: 'POST',
    credentials: 'include',
    headers,
    body: new URLSearchParams({ email }),
  });

  if (response.status === 409) throw new Error('Ten adres e-mail jest już używany.');
  if (response.status === 401) throw new Error('Sesja wygasła. Zaloguj się ponownie.');
  if (response.status === 403) throw new Error('Nie udało się potwierdzić sesji. Odśwież stronę.');
  if (!response.ok) throw new Error('Nie udało się zmienić adresu e-mail.');
}

export const updatePersonalAddress = (data: PersonalData) =>
  api.PATCH('/user/address', {
    body: {
      first_name: data.firstName,
      last_name: data.lastName,
      country: data.country,
      city: data.city,
      first_line: data.addressLine1,
      second_line: data.addressLine2,
      postal_code: data.postalCode,
    },
  });
