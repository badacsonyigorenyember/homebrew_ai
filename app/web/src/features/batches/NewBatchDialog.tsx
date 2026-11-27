import { useState } from 'react';
import { useNavigate } from 'react-router';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTrigger,
  DialogTitle,
} from '@/components/ui/dialog.tsx';
import { Button } from '@/components/ui/button.tsx';
import { NewBatchForm } from '@/features/batches/NewBatchForm.tsx';

export function NewBatchDialog() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button />}>New Batch</DialogTrigger>
      <DialogContent className="h-svh max-w-none content-start rounded-none sm:h-auto sm:max-w-lg sm:rounded-xl">
        <DialogHeader>
          <DialogTitle>New Batch</DialogTitle>
        </DialogHeader>
        <NewBatchForm
          onCreated={(batch) => {
            setOpen(false);
            navigate(`/batches/${batch.id}`);
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
