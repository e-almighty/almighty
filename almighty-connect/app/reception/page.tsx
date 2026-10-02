import ReceptionEntry from '@/components/reception-entry';
import {requireChatGPTUser} from '@/app/chatgpt-auth';
export const dynamic='force-dynamic';
export const metadata={title:'三宮の応答｜オールマイティ',manifest:'/reception.webmanifest',appleWebApp:{capable:true,title:'三宮の受付',statusBarStyle:'default' as const},icons:{icon:'/reception-icon.png',apple:'/reception-icon.png'}};
async function Authorized(){await requireChatGPTUser('/reception');return <ReceptionEntry role="staff"/>}
export default function Page(){return <Authorized/>}
