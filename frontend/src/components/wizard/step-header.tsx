interface StepHeaderProps {
  step: number;
  title: string;
  description: string;
}

export function StepHeader({ step, title, description }: StepHeaderProps) {
  return (
    <div className="mb-8">
      <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-primary">
        Step {step} of 7
      </p>
      <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
      <p className="mt-1 text-base text-muted-foreground">{description}</p>
    </div>
  );
}
