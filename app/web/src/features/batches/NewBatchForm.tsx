import z from 'zod';
import {
  ApiProblemError,
  type BrewableRecipe,
  type CreatedBatch,
  useBrewableBatches,
  useCreateBatch,
} from '@/features/batches/api';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Field,
  FieldGroup,
  FieldLabel,
  FieldError,
} from '@/components/ui/field';
import {
  NativeSelect,
  NativeSelectOption,
} from '@/components/ui/native-select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button.tsx';

const newBatchSchema = z.object({
  recipeId: z.number('Choose a recipe'),
  name: z.string().trim().min(1, 'Choose a name'),
  brewDate: z.iso.date(),
});

type NewBatchValues = z.infer<typeof newBatchSchema>;

function recipeLabel(recipe: BrewableRecipe): string {
  return [
    recipe.styleName ?? recipe.styleCode,
    recipe.og?.toFixed(3) ?? '-',
    recipe.abv != null ? `${recipe.abv}%` : '-',
    new Date(recipe.createdAt).getDate().toLocaleString(),
  ].join('·');
}

type NewBatchFormProps = { onCreated: (batch: CreatedBatch) => void };

const fieldNames: Partial<Record<string, keyof NewBatchValues>> = {
  RecipeId: 'recipeId',
  Name: 'name',
  BrewDate: 'brewDate',
};

export function NewBatchForm({ onCreated }: NewBatchFormProps) {
  const recipes = useBrewableBatches();
  const createBatch = useCreateBatch();
  const form = useForm<NewBatchValues>({
    resolver: zodResolver(newBatchSchema),
    defaultValues: { name: '', brewDate: '' },
  });
  const errors = form.formState.errors;

  function onSubmit(values: NewBatchValues) {
    createBatch.mutate(values, {
      onSuccess: onCreated,
      onError: (error) => {
        if (error instanceof ApiProblemError && error.problem.errors) {
          for (const [key, messages] of Object.entries(error.problem.errors)) {
            form.setError(fieldNames[key] ?? 'root.server', {
              message: messages.join(' '),
            });
          }
        } else {
          form.setError('root.server', { message: error.message });
        }
      },
    });
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <FieldGroup>
        <Field data-invalid={!!errors.recipeId}>
          <FieldLabel htmlFor={'recipeId'}>Recipe</FieldLabel>
          <NativeSelect
            id={'recipeId'}
            className={'w-full'}
            aria-invalid={!!errors.recipeId}
            {...form.register('recipeId', { valueAsNumber: true })}
            onChange={(event) => {
              const recipe = recipes.data?.find(
                (b) => b.id === Number(event.target.value),
              );
              if (recipe && !form.getFieldState('name').isDirty) {
                form.setValue('name', recipe.styleName ?? recipe.styleCode);
              }
            }}
          >
            <NativeSelectOption value={''}>
              {recipes.isPending ? 'Loading recipes...' : 'Choose a recipe'}
            </NativeSelectOption>
            {recipes.data?.map((recipe) => (
              <NativeSelectOption key={recipe.id} value={recipe.id}>
                {recipeLabel(recipe)}
              </NativeSelectOption>
            ))}
          </NativeSelect>
          <FieldError errors={[errors.recipeId]} />
        </Field>

        <Field data-invalid={!!errors.recipeId}>
          <FieldLabel htmlFor={'recipeId'}>Name</FieldLabel>
          <Input id={'name'} aria-invalid {...form.register('name')} />
          <FieldError errors={[errors.recipeId]} />
        </Field>
        <Field data-invalid={!!errors.recipeId}>
          <FieldLabel htmlFor={'recipeId'}>Brew date</FieldLabel>
          <Input
            id={'brewDate'}
            type={'date'}
            aria-invalid
            {...form.register('brewDate')}
          />
          <FieldError errors={[errors.recipeId]} />
        </Field>
        {errors.root?.server && (
          <p role={'alert'} className={'text-sm text-destructive'}>
            {errors.root.server.message}
          </p>
        )}
        <Button type={'submit'} disabled={createBatch.isPending}>
          Create batch
        </Button>
      </FieldGroup>
    </form>
  );
}
