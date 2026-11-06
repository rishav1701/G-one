import type {ReactNode} from 'react';
export function Table({children,label}:{children:ReactNode;label:string}){return <div className="table-scroll" role="region" aria-label="Scrollable data table" tabIndex={0}><table aria-label={label}>{children}</table></div>}
