import {render,screen} from '@testing-library/react';import {test,expect} from 'vitest';import {LevelBadge} from './LevelBadge';
test('level badge includes text and icon for LOW',()=>{render(<LevelBadge level="LOW"/>);expect(screen.getByText('LOW')).toBeInTheDocument()});
