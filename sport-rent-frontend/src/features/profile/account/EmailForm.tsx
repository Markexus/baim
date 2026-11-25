import { type SubmitEvent, useState } from 'react';

import FormActions from './FormActions.tsx';
import ProfileFormInput from './ProfileFormInput.tsx';

type EmailFormProps = {
  currentEmail: string;
  onSave: (email: string) => Promise<void>;
  onCancel: () => void;
};

export default function EmailForm({ currentEmail, onSave, onCancel }: EmailFormProps) {
  const [newEmail, setNewEmail] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedEmail = newEmail.trim();

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      alert('Proszę podać poprawny adres e-mail!');
      return;
    }
    if (trimmedEmail.toLowerCase() === currentEmail.toLowerCase()) {
      alert('Nowy adres e-mail nie może być taki sam jak obecny!');
      return;
    }
    setIsSaving(true);
    try {
      await onSave(trimmedEmail);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={(event) => void handleSubmit(event)}>
      <div className="mt-4 space-y-4">
        <ProfileFormInput
          type="email"
          value={newEmail}
          onChange={(event) => setNewEmail(event.target.value)}
          placeholder="Nowy adres e-mail"
          required
        />
      </div>
      <FormActions submitLabel={isSaving ? 'Zapisywanie…' : 'Zmień'} onCancel={onCancel} disabled={isSaving} />
    </form>
  );
}
