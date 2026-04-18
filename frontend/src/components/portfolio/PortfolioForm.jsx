import { useState } from 'react';
import styles from './PortfolioForm.module.css';

export default function PortfolioForm({ onSubmit, initial = {}, onCancel }) {
  const [name, setName] = useState(initial.name || '');
  const [description, setDescription] = useState(initial.description || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ name, description });
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.field}>
        <label htmlFor="pf-name">Portfolio Name</label>
        <input
          id="pf-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          maxLength={200}
          placeholder="e.g. Growth Portfolio"
        />
      </div>
      <div className={styles.field}>
        <label htmlFor="pf-desc">Description (optional)</label>
        <textarea
          id="pf-desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={1000}
          rows={3}
          placeholder="Describe your portfolio strategy..."
        />
      </div>
      <div className={styles.actions}>
        <button type="submit" className={styles.submitBtn}>
          {initial.name ? 'Update' : 'Create'} Portfolio
        </button>
        {onCancel && (
          <button type="button" className={styles.cancelBtn} onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
