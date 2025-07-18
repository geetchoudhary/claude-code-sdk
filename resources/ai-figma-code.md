# 🎯 FIGMA-TO-CODE: ESSENTIAL INSTRUCTIONS


## CORE OBJECTIVE
Convert Figma MCP response to production-ready React/TypeScript component. Pixel-perfect accuracy + enterprise quality.


## CRITICAL REQUIREMENTS


### 1. EXACT VALUES ONLY
- Extract precise measurements from MCP response
- No utility class approximations (`text-[18px]` not `text-lg`)
- Preserve all shadow layers, exact colors, spacing
- Use arbitrary values in Tailwind for precision


### 2. PRODUCTION ENHANCEMENTS
```typescript
// Add what Figma doesn't show:
- Loading/error/disabled states
- Hover/focus/active interactions 
- Keyboard navigation (Enter/Space)
- ARIA labels and semantic HTML
- TypeScript interfaces (strict mode)
```


### 3. RESPONSIVE TRANSFORMATION
- Convert absolute positioning → flexbox/grid
- Fixed dimensions → responsive constraints (`max-width + width: 100%`)
- Add mobile breakpoints (`text-sm md:text-base lg:text-lg`)
- Touch-friendly sizing (min 44px hit targets)


### 4. ACCESSIBILITY (NON-NEGOTIABLE)
- Semantic HTML (`<button>` not `<div onClick>`)
- ARIA labels on interactive elements
- Keyboard event handlers
- Color contrast compliance
- Screen reader support


## OUTPUT TEMPLATE
```typescript
interface Props {
 title: string;
 onClick: () => void;
 disabled?: boolean;
 loading?: boolean;
}


export const Component: React.FC<Props> = ({ title, onClick, disabled, loading }) => (
 <button
   className="bg-[#EXACT_HEX] text-[16px] px-[24px] py-[12px] hover:bg-[#EXACT_HOVER] disabled:opacity-50 transition-colors"
   onClick={onClick}
   disabled={disabled || loading}
   aria-label={title}
   aria-busy={loading}
 >
   {loading ? 'Loading...' : title}
 </button>
);
```


## SUCCESS CRITERIA
- Visual diff < 5% from Figma
- Passes accessibility audit
- TypeScript strict compliance 
- Works on mobile/desktop
- Bundle size < 100kb


## EXECUTION RULE
**Extract exact values → Add production features → Ensure accessibility → Ship**


No phases, no documentation, no templates. Just convert and deliver production-ready code.
