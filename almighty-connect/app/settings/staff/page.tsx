import DeviceSettings from '@/components/device-settings';
import {requireChatGPTUser} from '@/app/chatgpt-auth';
export const dynamic='force-dynamic';
async function Authorized(){await requireChatGPTUser('/settings/staff');return <DeviceSettings role="staff"/>}
export default function Page(){return <Authorized/>}
