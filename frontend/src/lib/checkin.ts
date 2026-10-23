import { siteHour } from './format'

function pick(lines: string[]): string {
  return lines[Math.floor(Math.random() * lines.length)]
}

/** 签到成功后的问候，按站点时区选早上/中午/下午/晚上。 */
export function checkInGreeting(name: string): string {
  const who = name.trim() || '朋友'
  const hour = siteHour()

  if (hour >= 5 && hour < 11) {
    return pick([
      `早上好，${who}。又是新的一天。`,
      `早，${who}。今天也来看看吧。`,
    ])
  }
  if (hour >= 11 && hour < 14) {
    return pick([
      `中午好，${who}。吃了吗？`,
      `午饭时间到，${who}。别忘了吃饭。`,
    ])
  }
  if (hour >= 14 && hour < 18) {
    return pick([
      `下午好，${who}。`,
      `下午好，${who}。喝口水，歇一会儿。`,
    ])
  }
  if (hour >= 18 && hour < 23) {
    return pick([
      `晚上好，${who}。今天辛苦了。`,
      `晚上好，${who}。`,
    ])
  }
  return pick([
    `夜深了，${who}。早点休息。`,
    `还没睡吗，${who}？`,
  ])
}
