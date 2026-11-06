import {render,screen} from '@testing-library/react';
import {test,expect} from 'vitest';
import {LevelBadge} from './LevelBadge';

test.each([
 ['LOW','LOW'],['LOW_MEDIUM','LOW MEDIUM'],['MEDIUM','MEDIUM'],['HIGH','HIGH'],
 ['INCOMPLETE','Assessment limited'],['STALE','STALE'],['NO_DATA','No data'],
] as const)('shows the %s level with readable text', (level,label)=>{
 render(<LevelBadge level={level}/>);
 expect(screen.getByText(label)).toBeInTheDocument();
 expect(screen.getByText(label).closest('.badge')).toBeInTheDocument();
});
