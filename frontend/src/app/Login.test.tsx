import {render,screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {expect,test,vi} from 'vitest';

const mocks=vi.hoisted(()=>({login:vi.fn()}));
vi.mock('./Auth',()=>({useAuth:()=>({login:mocks.login})}));

import Login from './Login';

test('explains which seeded role supports manual observation entry',()=>{
 render(<MemoryRouter><Login/></MemoryRouter>);
 expect(screen.getByText(/For patient records and manual observations/)).toBeInTheDocument();
 expect(screen.getByText(/ADMIN account manages demonstration controls and cannot enter clinical data/)).toBeInTheDocument();
});
