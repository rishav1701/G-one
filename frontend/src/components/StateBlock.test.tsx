import {render,screen} from '@testing-library/react';import {test,expect} from 'vitest';import {StateBlock} from './StateBlock';
test.each(['loading','empty','error','stale','forbidden','no-data'] as const)('StateBlock renders the %s state',state=>{render(<StateBlock state={state}/>);expect(screen.getByText(/./)).toBeInTheDocument()});
