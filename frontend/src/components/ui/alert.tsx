import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

const Alert = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & {
    variant?: 'default' | 'destructive';
  }
>(({ className, variant = 'default', ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'relative w-full rounded-lg border p-4',
      {
        'border-gray-200 text-gray-900 bg-gray-50': variant === 'default',
        'border-red-200 text-red-800 bg-red-50': variant === 'destructive',
      },
      className
    )}
    {...props}
  />
));
Alert.displayName = 'Alert';

const AlertDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('text-sm [&_p]:leading-relaxed', className)}
    {...props}
  />
));
AlertDescription.displayName = 'AlertDescription';

export { Alert, AlertDescription };