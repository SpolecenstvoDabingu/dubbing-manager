ANNOUNCEMENT = lambda id,t: f"/announcement type:{t} id:{id}"

EPISODE_ANNOUNCEMENT = lambda id: ANNOUNCEMENT(id, 'episode')

SCENE_ANNOUNCEMENT = lambda id: ANNOUNCEMENT(id, 'scene')