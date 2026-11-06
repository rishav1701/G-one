import {expect,test,Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';
const username=process.env.E2E_USERNAME||'phaseadmin';
const password=process.env.E2E_PASSWORD||'Phase1-Rotated-Passphrase-2026!';
const screenshots=path.resolve(process.cwd(),'..','docs','screens','phase-6');
const sizes=[[1440,900],[1024,768],[390,844]] as const;
async function capture(page:Page,name:string){for(const [width,height] of sizes){await page.setViewportSize({width,height});await expect(page.getByText('SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.')).toBeVisible();const pageWidth=await page.evaluate(()=>({width:document.body.scrollWidth,clipped:getComputedStyle(document.documentElement).overflowX==='clip'}));expect(pageWidth.width<=width&&pageWidth.clipped,`${name} page-level overflow at ${width}`).toBeTruthy();await page.screenshot({path:path.join(screenshots,`${name}-${width}x${height}.png`),fullPage:true});const results=await new AxeBuilder({page}).analyze();const serious=results.violations.filter(item=>item.impact==='serious'||item.impact==='critical');expect(serious.map(item=>({id:item.id,impact:item.impact,help:item.help,nodes:item.nodes.map(node=>node.target)})),`${name} ${width}x${height} axe violations`).toEqual([])}}
test('Phase 6 analytics, lab display, and no-model state',async({page})=>{
 test.setTimeout(90000);fs.mkdirSync(screenshots,{recursive:true});const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/login');await page.getByLabel('Username').fill(username);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Sign in'}).click();await expect(page.getByRole('heading',{name:'Dashboard'})).toBeVisible();
 await page.goto('/analytics');await expect(page.getByRole('heading',{name:'Live operational metrics'})).toBeVisible();await expect(page.getByRole('heading',{name:'Simulation scenario outcomes'})).toBeVisible();await expect(page.getByRole('heading',{name:'Model evaluation'})).toBeVisible();await expect(page.getByText('Not available: no trained model is deployed.')).toBeVisible();await expect(page.getByText('Stable observations')).toBeVisible();await capture(page,'analytics');
 await page.goto('/patients?q=SIM-000001');const row=page.getByRole('row').filter({hasText:'SIM-000001'});await expect(row).toBeVisible();await row.click();await expect(page.getByRole('heading',{name:'Model estimate'})).toBeVisible();await expect(page.getByText('No trained ML model is deployed.')).toBeVisible();await capture(page,'patient-model-none');
 await page.getByRole('button',{name:'Labs',exact:true}).click();await expect(page.getByRole('heading',{name:'Labs'})).toBeVisible();await expect(page.getByRole('cell',{name:'Haemoglobin'})).toBeVisible();await expect(page.getByRole('cell',{name:'C-reactive protein'})).toBeVisible();await capture(page,'patient-labs');
 expect(errors,errors.join('\n')).toEqual([]);
});
