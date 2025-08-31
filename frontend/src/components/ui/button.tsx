import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils.js';
import { type VariantProps, cva } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: '',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(
          buttonVariants({ variant, size }),
          // Default fallback styles for when CSS variables don't work
          (variant === 'default' || !variant) && !className?.includes('bg-') && 'bg-blue-600 text-white hover:bg-blue-700',
          variant === 'outline' && !className?.includes('bg-') && 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
          variant === 'secondary' && !className?.includes('bg-') && 'bg-gray-100 text-gray-900 hover:bg-gray-200',
          variant === 'ghost' && !className?.includes('bg-') && 'hover:bg-gray-100',
          variant === 'destructive' && !className?.includes('bg-') && 'bg-red-600 text-white hover:bg-red-700',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };