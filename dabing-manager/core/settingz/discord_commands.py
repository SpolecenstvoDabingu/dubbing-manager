ANNOUNCEMENT = lambda id,t: f"/announcement type:{t} id:{id}"
NOTIFY = lambda id,t: f"/notify type:{t} id:{id}"

EPISODE_ANNOUNCEMENT = lambda id: ANNOUNCEMENT(id, 'episode')

SCENE_ANNOUNCEMENT = lambda id: ANNOUNCEMENT(id, 'scene')

EPISODE_NOTIFY = lambda id: NOTIFY(id, 'episode')

SCENE_NOTIFY = lambda id: NOTIFY(id, 'scene')