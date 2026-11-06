import {test,expect} from '@playwright/test';
import {createHash,randomBytes} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
const username=process.env.E2E_USERNAME||'phaseadmin';
const oldPassword=process.env.E2E_PASSWORD;
if(!oldPassword)throw new Error('Set E2E_PASSWORD to the generated local demo admin password before running browser tests.');
const newPassword=`${randomBytes(24).toString('base64url')}aA1!`;
const wrongPassword=randomBytes(24).toString('base64url');
const repo=path.resolve(process.cwd(),'..');
const screenshots=path.join(repo,'docs','screens','phase-1');
const psql=process.env.PSQL_PATH||path.join(repo,'.tools','postgresql-17','bin','psql.exe');
function sql(statement:string){execFileSync(psql,['-h','127.0.0.1','-U','postgres','-d','gone','-v','ON_ERROR_STOP=1','-c',statement],{stdio:'pipe',env:{...process.env,PGPASSWORD:''}})}

test('login, change password, no-CSRF rejection, and login at three viewports',async({page})=>{
  await page.goto('/login');
  for(const [width,height] of [[1440,900],[1024,768],[390,844]]){
    await page.setViewportSize({width,height});
    await expect(page.getByText('SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.')).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();await page.screenshot({path:path.join(screenshots,`login-${width}.png`),fullPage:true});
  }
  await page.setViewportSize({width:1440,height:900});
  await page.getByLabel('Username').fill(username);await page.getByLabel('Password',{exact:true}).fill(oldPassword);await page.getByRole('button',{name:'Sign in'}).click();
  await expect(page.getByRole('heading',{name:'Dashboard'})).toBeVisible();
  const cookie=(await page.context().cookies()).find(c=>c.name==='g_one_session');expect(cookie?.httpOnly).toBeTruthy();expect(cookie?.sameSite).toBe('Lax');
  for(const [width,height] of [[1440,900],[1024,768],[390,844]]){
    await page.setViewportSize({width,height});
    await expect(page.getByText('SIMULATED DATA. DEMONSTRATION ONLY. NOT FOR CLINICAL USE.')).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();await page.screenshot({path:path.join(screenshots,`shell-${width}.png`),fullPage:true});
  }
  const csrfResult=await page.request.post('/api/v1/auth/logout');expect(csrfResult.status()).toBe(403);
  await page.locator('details.user-menu summary').click();await page.getByRole('button',{name:'Change password'}).click();
  await page.getByLabel('Current password').fill(oldPassword);await page.getByLabel('New password').fill(newPassword);await page.getByRole('button',{name:'Save password'}).click();
  await expect(page.getByText('Password changed.')).toBeVisible();await page.getByRole('button',{name:'Cancel'}).click();
  await page.getByRole('button',{name:'Sign out'}).click();await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel('Username').fill(username);await page.getByLabel('Password',{exact:true}).fill(oldPassword);await page.getByRole('button',{name:'Sign in'}).click();
  await expect(page.getByRole('alert')).toContainText('Unable to sign in with those credentials');
  await page.getByLabel('Password',{exact:true}).fill(newPassword);await page.getByRole('button',{name:'Sign in'}).click();await expect(page.getByRole('heading',{name:'Dashboard'})).toBeVisible();
  await page.locator('details.user-menu summary').click();await page.getByRole('button',{name:'Change password'}).click();await page.getByLabel('Current password').fill(newPassword);await page.getByLabel('New password').fill(oldPassword);await page.getByRole('button',{name:'Save password'}).click();await expect(page.getByText('Password changed.')).toBeVisible();await page.getByRole('button',{name:'Cancel'}).click();
});

test('expired server-side session sends user back to login',async({page})=>{
  await page.goto('/login');await page.getByLabel('Username').fill(username);await page.getByLabel('Password',{exact:true}).fill(oldPassword);await page.getByRole('button',{name:'Sign in'}).click();await expect(page.getByRole('heading',{name:'Dashboard'})).toBeVisible();
  const token=(await page.context().cookies()).find(c=>c.name==='g_one_session')?.value;expect(token).toBeTruthy();
  const hash=createHash('sha256').update(token!).digest('hex');sql(`UPDATE session SET expires_at=now()-interval '1 minute' WHERE token_hash='${hash}'`);
  await page.reload();await expect(page).toHaveURL(/\/login$/);
});

test('temporary account lockout is shown after failed attempts',async({page})=>{
  sql(`UPDATE app_user SET failed_logins=0,locked_until=NULL WHERE username='${username.replaceAll("'","''")}'`);
  await page.goto('/login');await page.getByLabel('Username').fill(username);
  for(let attempt=0;attempt<6;attempt++){
    await page.getByLabel('Password',{exact:true}).fill(wrongPassword);await page.getByRole('button',{name:'Sign in'}).click();
    if(attempt<5) await expect(page.getByRole('alert')).toContainText('Unable to sign in with those credentials');
  }
  await expect(page.getByRole('alert')).toContainText('Account temporarily locked. Try again later');
  sql(`UPDATE app_user SET failed_logins=0,locked_until=NULL WHERE username='${username.replaceAll("'","''")}'`);
});






