from tutorial.control import TutorialProxyHolder
from tutorial.control import functional
from tutorial.logger import LOG_DEBUG
STATE_LOADING = 0
STATE_WAIT_SCENE = 1
STATE_NEXT_SCENE = 2
STATE_LEARNING = 3
STATE_RUN_EFFECTS = 4

class _TutorialState(TutorialProxyHolder):

    def _tick(self):
        raise NotImplementedError, 'Method not implemented'

    def allowedToSwitch(self):
        return True

    def mouseClicked(self, _):
        pass


class TutorialStateLoading(_TutorialState):

    def _tick(self):
        self._gui.clear()


class TutorialStateWaitScene(_TutorialState):

    def __init__(self):
        super(TutorialStateWaitScene, self).__init__()
        self._isAllowedToSwitch = False

    def _tick(self):
        nextScene = self._tutorial.getNextScene()
        if nextScene.getID() == self._gui.getSceneID():
            self._tutorial.setFunctionalScene(nextScene)
            postEffects = nextScene.getPostEffects()
            postEffects = filter(lambda item: functional.FunctionalConditions(item.getConditions()).allConditionsOk(), postEffects)
            self._isAllowedToSwitch = True
            if len(postEffects):
                self._tutorial.storeEffectsInQueue(postEffects)
            else:
                self._tutorial.evaluateState()

    def allowedToSwitch(self):
        return self._isAllowedToSwitch


class TutorialStateNextScene(_TutorialState):

    def _tick(self):
        nextScene = self._tutorial.getNextScene()
        currentScene = self._gui.getSceneID()
        if currentScene is not None:
            if nextScene.getID() != currentScene:
                self._gui.goToScene(nextScene.getID())
            self._tutorial.setState(STATE_WAIT_SCENE)
        return


class TutorialStateLearning(_TutorialState):

    def __init__(self):
        super(TutorialStateLearning, self).__init__()

    def _tick(self):
        scene = self._tutorial.getFunctionalScene()
        scene.update()

    def mouseClicked(self, event):
        scene = self._tutorial.getFunctionalScene()
        action = scene.getAction(event.targetID)
        if action is not None:
            self._tutorial.storeEffectsInQueue(action.getEffects())
        return


class TutorialStateRunEffects(_TutorialState):

    def __init__(self):
        super(TutorialStateRunEffects, self).__init__()
        self._current = None
        return

    def _tick(self):
        if self._current is None or not self._current.isStillRunning():
            self._current = None
            stop = False
            while not stop:
                currentEffect = self._tutorial.getFirstElementOfTop()
                if currentEffect is None:
                    stop = True
                    self._tutorial.evaluateState()
                elif currentEffect.isAllConditionsOK():
                    LOG_DEBUG('Trigger effect', currentEffect._effect)
                    currentEffect.triggerEffect()
                    stop = not currentEffect.isInstantaneous()
                    if stop:
                        self._current = currentEffect

        return

    def allowedToSwitch(self):
        return False

    def mouseClicked(self, event):
        if self._current is not None and self._current.isStillRunning():
            target = self._current.getTarget()
            if target is not None:
                action = target.getAction(event.targetID)
                if action is not None:
                    self._tutorial.storeEffectsInQueue(action.getEffects(), benefit=True)
                    self._current.stop()
                    self._current = None
        else:
            scene = self._tutorial.getFunctionalScene()
            action = scene.getAction(event.targetID)
            if action is not None:
                self._tutorial.storeEffectsInQueue(action.getEffects())
        return


_statesFactory = {STATE_LOADING: TutorialStateLoading,
 STATE_WAIT_SCENE: TutorialStateWaitScene,
 STATE_NEXT_SCENE: TutorialStateNextScene,
 STATE_LEARNING: TutorialStateLearning,
 STATE_RUN_EFFECTS: TutorialStateRunEffects}

def factory(stateIndex):
    return _statesFactory.get(stateIndex)
